import os
import shutil
import pytest
from resume.compiler import ResumeCompiler

@pytest.fixture
def compiler():
    return ResumeCompiler()

@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "output"

DEFAULT_SUMMARY = (
    "Dynamic Data Engineer with 9+ years designing ETL pipelines "
    "using Azure Databricks, Microsoft Fabric, and AWS. "
    "Expert in Lake House architectures and CI/CD for data workflows."
)

DEFAULT_SKILLS = r"""\textbf{Cloud \& Data}\\
Azure Databricks \textbullet{} Fabric\\
AWS (Glue, EMR, Redshift)\\
Snowflake \textbullet{} Delta Lake\\[0.25cm]

\textbf{Programming}\\
Python \textbullet{} PySpark \textbullet{} SQL\\
Scala \textbullet{} Java \textbullet{} Julia\\[0.25cm]

\textbf{DevOps \& Tools}\\
Terraform \textbullet{} Docker \textbullet{} K8s\\
Airflow \textbullet{} dbt \textbullet{} Git\\
Azure DevOps \textbullet{} Jenkins"""


class TestTemplateLoading:
    def test_loads_base_template(self, compiler):
        template = compiler.load_template()
        assert "%%SUMMARY%%" in template
        assert "%%SKILLS_ORDER%%" in template
        assert "%%EXPERIENCE_HIGHLIGHTS%%" in template
        assert "%%RELEVANT_PROJECTS%%" in template

    def test_fill_template(self, compiler):
        filled = compiler.fill_template(
            summary=DEFAULT_SUMMARY,
            skills=DEFAULT_SKILLS,
            experience="\\textbf{Test Job}",
        )
        assert "%%SUMMARY%%" not in filled
        assert "%%SKILLS_ORDER%%" not in filled
        assert "%%EXPERIENCE_HIGHLIGHTS%%" not in filled
        assert "Dynamic Data Engineer" in filled

    def test_fill_with_none_uses_defaults(self, compiler):
        filled = compiler.fill_template()
        assert "%%SUMMARY%%" not in filled
        assert "%%SKILLS_ORDER%%" not in filled
        assert "%%EXPERIENCE_HIGHLIGHTS%%" not in filled
        assert "Dynamic Data Engineer" in filled
        assert "Capgemini" in filled


class TestCompilation:
    @pytest.mark.skipif(
        shutil.which("pdflatex") is None,
        reason="pdflatex not installed"
    )
    def test_compile_produces_pdf(self, compiler, output_dir):
        filled = compiler.fill_template()
        pdf_path = compiler.compile(filled, str(output_dir))
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        assert os.path.getsize(pdf_path) > 0

    def test_compile_invalid_latex_returns_none(self, compiler, output_dir):
        result = compiler.compile(
            r"\documentclass{article}\begin{document}\invalid{",
            str(output_dir)
        )
        assert result is None


class TestFallback:
    @pytest.mark.skipif(
        shutil.which("pdflatex") is None,
        reason="pdflatex not installed"
    )
    def test_fallback_on_bad_tailored_tex(self, compiler, output_dir):
        pdf_path = compiler.compile_with_fallback(
            tailored_tex=r"\documentclass{article}\begin{document}\invalid{",
            output_dir=str(output_dir),
        )
        # Should fall back to base resume with defaults
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
