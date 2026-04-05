"""LinkedIn Easy Apply automation module."""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from linkedin.browser import random_delay, safe_click

logger = logging.getLogger(__name__)

SUPPORTED_FIELD_TYPES = {"text", "select", "radio", "checkbox", "file", "textarea"}


@dataclass
class ApplicationResult:
    """Result of a LinkedIn Easy Apply submission."""

    success: bool
    job_url: str
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    fields_filled: list = field(default_factory=list)


def is_easy_apply_supported(fields: list[dict]) -> bool:
    """Check if all field types in the form are supported.

    Args:
        fields: List of field dicts with at least a 'type' key.

    Returns:
        True if every field type is in SUPPORTED_FIELD_TYPES, False otherwise.
    """
    return all(f.get("type") in SUPPORTED_FIELD_TYPES for f in fields)


async def detect_form_fields(page) -> list[dict]:
    """Detect form fields inside the LinkedIn Easy Apply modal.

    Args:
        page: A Playwright page object with an open Easy Apply modal.

    Returns:
        List of dicts describing each detected field:
        {type, label, selector, required, options (for select/radio)}
    """
    fields = []

    # Wait for the modal to be present
    modal_selector = "div[data-test-modal], div.jobs-easy-apply-modal"
    try:
        await page.wait_for_selector(modal_selector, timeout=10000)
    except Exception:
        logger.warning("Easy Apply modal not found within timeout")
        return fields

    # Text inputs and textareas
    input_elements = await page.query_selector_all(
        "input[type='text'], input[type='email'], input[type='tel'], input[type='number']"
    )
    for el in input_elements:
        label = await _get_label(page, el)
        selector = await _build_selector(el)
        fields.append({"type": "text", "label": label, "selector": selector, "required": await _is_required(el)})

    textarea_elements = await page.query_selector_all("textarea")
    for el in textarea_elements:
        label = await _get_label(page, el)
        selector = await _build_selector(el)
        fields.append({"type": "textarea", "label": label, "selector": selector, "required": await _is_required(el)})

    # Select dropdowns
    select_elements = await page.query_selector_all("select")
    for el in select_elements:
        label = await _get_label(page, el)
        selector = await _build_selector(el)
        options = await el.evaluate("el => Array.from(el.options).map(o => o.value)")
        fields.append({
            "type": "select",
            "label": label,
            "selector": selector,
            "required": await _is_required(el),
            "options": options,
        })

    # Radio buttons (group by name)
    radio_elements = await page.query_selector_all("input[type='radio']")
    radio_groups: dict[str, dict] = {}
    for el in radio_elements:
        name = await el.get_attribute("name") or ""
        if name not in radio_groups:
            label = await _get_label(page, el)
            radio_groups[name] = {
                "type": "radio",
                "label": label,
                "selector": f"input[type='radio'][name='{name}']",
                "required": await _is_required(el),
                "options": [],
            }
        value = await el.get_attribute("value") or ""
        radio_groups[name]["options"].append(value)
    fields.extend(radio_groups.values())

    # Checkboxes
    checkbox_elements = await page.query_selector_all("input[type='checkbox']")
    for el in checkbox_elements:
        label = await _get_label(page, el)
        selector = await _build_selector(el)
        fields.append({"type": "checkbox", "label": label, "selector": selector, "required": await _is_required(el)})

    # File inputs
    file_elements = await page.query_selector_all("input[type='file']")
    for el in file_elements:
        label = await _get_label(page, el)
        selector = await _build_selector(el)
        fields.append({"type": "file", "label": label, "selector": selector, "required": await _is_required(el)})

    logger.info("Detected %d form fields", len(fields))
    return fields


async def fill_field(page, field_info: dict, value) -> bool:
    """Fill a single form field based on its type.

    Args:
        page: Playwright page object.
        field_info: Dict with at least 'type' and 'selector' keys.
        value: Value to fill (str, bool, or Path for file fields).

    Returns:
        True if the field was filled successfully, False otherwise.
    """
    field_type = field_info.get("type")
    selector = field_info.get("selector", "")

    try:
        if field_type == "text" or field_type == "textarea":
            await page.fill(selector, str(value))

        elif field_type == "select":
            await page.select_option(selector, str(value))

        elif field_type == "radio":
            # selector is like input[type='radio'][name='...'], value picks which one
            await page.check(f"{selector}[value='{value}']")

        elif field_type == "checkbox":
            if value:
                await page.check(selector)
            else:
                await page.uncheck(selector)

        elif field_type == "file":
            await page.set_input_files(selector, str(value))

        else:
            logger.warning("Unsupported field type: %s", field_type)
            return False

        await random_delay(0.3, 0.8)
        logger.debug("Filled field '%s' (type=%s)", field_info.get("label"), field_type)
        return True

    except Exception as exc:
        logger.error("Failed to fill field '%s': %s", field_info.get("label"), exc)
        return False


async def submit_easy_apply(
    page,
    job_url: str,
    resume_path: str,
    answers: Optional[dict] = None,
    screenshot_dir: Optional[str] = None,
) -> ApplicationResult:
    """Execute the complete LinkedIn Easy Apply flow.

    Args:
        page: Playwright page object (should be on the job listing page).
        job_url: URL of the job listing.
        resume_path: Absolute path to the resume file.
        answers: Optional dict mapping field labels to answers.
        screenshot_dir: Optional directory to save screenshots.

    Returns:
        ApplicationResult with success status and metadata.
    """
    answers = answers or {}
    fields_filled: list[str] = []
    screenshot_path: Optional[str] = None

    try:
        # Navigate to job if not already there
        if page.url != job_url:
            await page.goto(job_url, wait_until="domcontentloaded")
            await random_delay(2.0, 4.0)

        # Click the Easy Apply button
        easy_apply_clicked = await safe_click(page, "button.jobs-apply-button")
        if not easy_apply_clicked:
            # Try alternative selectors
            easy_apply_clicked = await safe_click(
                page, "[data-control-name='jobdetails_topcard_inapply']"
            )
        if not easy_apply_clicked:
            return ApplicationResult(
                success=False,
                job_url=job_url,
                error="Could not find or click the Easy Apply button",
            )

        await random_delay(1.5, 3.0)

        # Multi-step form loop
        max_steps = 10
        for step in range(max_steps):
            logger.info("Easy Apply step %d", step + 1)

            # Detect fields on current step
            detected_fields = await detect_form_fields(page)

            if not is_easy_apply_supported(detected_fields):
                unsupported = [f["type"] for f in detected_fields if f.get("type") not in SUPPORTED_FIELD_TYPES]
                return ApplicationResult(
                    success=False,
                    job_url=job_url,
                    error=f"Unsupported form field type(s): {', '.join(unsupported)}",
                    fields_filled=fields_filled,
                )

            # Fill each detected field
            for fld in detected_fields:
                label = fld.get("label", "")
                ftype = fld.get("type")

                # File fields → use resume
                if ftype == "file":
                    filled = await fill_field(page, fld, resume_path)
                # Use provided answers dict (case-insensitive label match)
                elif label.lower() in {k.lower() for k in answers}:
                    matched_key = next(k for k in answers if k.lower() == label.lower())
                    filled = await fill_field(page, fld, answers[matched_key])
                else:
                    # Skip optional unanswered fields
                    if not fld.get("required"):
                        continue
                    logger.warning("No answer for required field: %s", label)
                    filled = False

                if filled:
                    fields_filled.append(label)

            # Take screenshot if requested
            if screenshot_dir:
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = str(Path(screenshot_dir) / f"step_{step + 1}.png")
                await page.screenshot(path=screenshot_path)

            # Check for Submit button
            submit_btn = await page.query_selector("button[aria-label='Submit application']")
            if submit_btn:
                await submit_btn.click()
                await random_delay(2.0, 4.0)
                logger.info("Application submitted successfully")
                break

            # Click Next/Continue button
            next_clicked = await safe_click(page, "button[aria-label='Continue to next step']")
            if not next_clicked:
                next_clicked = await safe_click(page, "button[aria-label='Review your application']")
            if not next_clicked:
                return ApplicationResult(
                    success=False,
                    job_url=job_url,
                    error="Could not find Next or Submit button",
                    fields_filled=fields_filled,
                    screenshot_path=screenshot_path,
                )

            await random_delay(1.0, 2.5)
        else:
            return ApplicationResult(
                success=False,
                job_url=job_url,
                error=f"Exceeded maximum steps ({max_steps}) without submitting",
                fields_filled=fields_filled,
                screenshot_path=screenshot_path,
            )

        return ApplicationResult(
            success=True,
            job_url=job_url,
            screenshot_path=screenshot_path,
            fields_filled=fields_filled,
        )

    except Exception as exc:
        logger.exception("Unexpected error during Easy Apply: %s", exc)
        return ApplicationResult(
            success=False,
            job_url=job_url,
            error=str(exc),
            fields_filled=fields_filled,
            screenshot_path=screenshot_path,
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_label(page, element) -> str:
    """Try to find a label for the given element."""
    try:
        el_id = await element.get_attribute("id")
        if el_id:
            label_el = await page.query_selector(f"label[for='{el_id}']")
            if label_el:
                return (await label_el.inner_text()).strip()
        # Fallback: aria-label
        aria = await element.get_attribute("aria-label")
        if aria:
            return aria.strip()
        # Fallback: placeholder
        placeholder = await element.get_attribute("placeholder")
        if placeholder:
            return placeholder.strip()
    except Exception:
        pass
    return ""


async def _build_selector(element) -> str:
    """Build a CSS selector for the element using its id or name."""
    try:
        el_id = await element.get_attribute("id")
        if el_id:
            return f"#{el_id}"
        name = await element.get_attribute("name")
        tag = await element.evaluate("el => el.tagName.toLowerCase()")
        if name:
            return f"{tag}[name='{name}']"
    except Exception:
        pass
    return ""


async def _is_required(element) -> bool:
    """Return True if the element has a required attribute."""
    try:
        required = await element.get_attribute("required")
        return required is not None
    except Exception:
        return False
