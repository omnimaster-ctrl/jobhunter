"""LaTeX Resume Compiler — fills template zones and produces a PDF."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class ResumeCompiler:
    """Compile a LaTeX resume from a template with replaceable zones."""

    DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"
    TEMPLATE_FILENAME = "base_resume.tex"
    SUPPORT_FILES = ["daveProfile.png"]

    def __init__(self, template_dir: Optional[str] = None) -> None:
        self.template_dir = Path(template_dir) if template_dir else self.DEFAULT_TEMPLATE_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_template(self) -> str:
        """Read and return the raw LaTeX template string."""
        template_path = self.template_dir / self.TEMPLATE_FILENAME
        return template_path.read_text(encoding="utf-8")

    def fill_template(
        self,
        summary: Optional[str] = None,
        skills: Optional[str] = None,
        experience: Optional[str] = None,
        projects: Optional[str] = None,
    ) -> str:
        """Replace %%ZONE%% markers in the template.

        Any argument that is None falls back to the default content from
        _get_defaults().  The ``projects`` zone is replaced with an empty
        string when None (it is optional in the template).
        """
        defaults = self._get_defaults()
        tex = self.load_template()

        tex = tex.replace("%%SUMMARY%%", summary if summary is not None else defaults["summary"])
        tex = tex.replace("%%SKILLS_ORDER%%", skills if skills is not None else defaults["skills"])
        tex = tex.replace(
            "%%EXPERIENCE_HIGHLIGHTS%%",
            experience if experience is not None else defaults["experience"],
        )
        tex = tex.replace(
            "%%RELEVANT_PROJECTS%%",
            projects if projects is not None else "",
        )
        return tex

    def compile(self, tex_source: str, output_dir: str) -> Optional[str]:
        """Write *tex_source* to a temp dir, run pdflatex, copy PDF to *output_dir*.

        Returns the absolute path to the produced PDF, or None on failure.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            # Copy support files (images, etc.) so LaTeX can find them
            for fname in self.SUPPORT_FILES:
                src = self.template_dir / fname
                if src.exists():
                    shutil.copy2(src, tmp_path / fname)

            tex_file = tmp_path / "resume.tex"
            tex_file.write_text(tex_source, encoding="utf-8")

            try:
                result = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        str(tex_file),
                    ],
                    cwd=str(tmp_path),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None

            if result.returncode != 0:
                return None

            produced_pdf = tmp_path / "resume.pdf"
            if not produced_pdf.exists():
                return None

            dest_pdf = output_path / "resume.pdf"
            shutil.copy2(produced_pdf, dest_pdf)
            return str(dest_pdf)

    def compile_with_fallback(
        self,
        tailored_tex: str,
        output_dir: str,
    ) -> Optional[str]:
        """Try to compile *tailored_tex*; fall back to the base resume on failure."""
        pdf_path = self.compile(tailored_tex, output_dir)
        if pdf_path is not None:
            return pdf_path

        # Fallback: compile default resume
        default_tex = self.fill_template()
        return self.compile(default_tex, output_dir)

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------

    def _get_defaults(self) -> dict:
        """Return the original resume content for every template zone."""
        return {
            "summary": (
                "Dynamic Data Engineer with 9+ years designing ETL pipelines "
                "using Azure Databricks, Microsoft Fabric, and AWS. "
                "Expert in Lake House architectures and CI/CD for data workflows."
            ),
            "skills": r"""\textbf{Cloud \& Data}\\
Azure Databricks \textbullet{} Fabric\\
AWS (Glue, EMR, Redshift)\\
Snowflake \textbullet{} Delta Lake\\[0.25cm]

\textbf{Programming}\\
Python \textbullet{} PySpark \textbullet{} SQL\\
Scala \textbullet{} Java \textbullet{} Julia\\[0.25cm]

\textbf{DevOps \& Tools}\\
Terraform \textbullet{} Docker \textbullet{} K8s\\
Airflow \textbullet{} dbt \textbullet{} Git\\
Azure DevOps \textbullet{} Jenkins""",
            "experience": r"""\textbf{Data Engineer} \hfill \textbf{Jun 2025 - Present}\\
{\color{accentgreen}Capgemini} | Remote
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Orchestrate end-to-end ETL/ELT pipelines with Microsoft Fabric, Azure Data Factory, and Terraform
\item Leverage Azure Databricks ecosystem (Delta Lake, Delta Live Tables, MLflow) for scalable analytics
\item Build modular data transformations using dbt with automated testing and documentation
\item Design and schedule complex workflows with Airflow for batch and streaming pipelines
\item Develop AWS data solutions using Glue, EMR, Redshift, and S3 for multi-cloud architectures
\end{itemize}

\vspace{0.1cm}
\textbf{Data Engineer} \hfill \textbf{Jul 2024 - Jun 2025}\\
{\color{accentgreen}Hexaware Technologies} | Remote
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Implement Lake House architecture with Azure Purview and Snowflake
\item Design ETL pipelines using Data Factory and Dataflow Gen2 for scalable ingestion
\item Integrate Microsoft Fabric with Azure Databricks, Functions, and Synapse
\end{itemize}

\vspace{0.1cm}
\textbf{Sr Data Engineer (Freelancer Contractor)} \hfill \textbf{Jan 2023 - Jan 2025}\\
{\color{accentgreen}Sherwin Williams} | Remote, USA
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Design and orchestrate ETL pipelines using Data Factory and Dataflow Gen2 for scalable data ingestion and transformation
\item Develop and maintain Notebooks for complex data processing and analytics using PySpark and SQL
\item Integrate Microsoft Fabric with external services like Azure Databricks, Azure Functions, and Synapse for advanced processing
\item Implement CI/CD pipelines for Fabric-based workflows using Azure DevOps and Infrastructure as Code (IaC) tools like Terraform
\item Employed Lake House architecture with Azure Purview and Snowflake for unified analytics
\end{itemize}

\vspace{0.1cm}
\textbf{Data Engineer} \hfill \textbf{May 2024 - Jul 2024}\\
{\color{accentgreen}Eviden} | Remote
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Designed scalable data flows in Python, SQL, and Scala with Spark Streaming
\item Built parameterized workflows and incremental loads using Airflow
\item Integrated monitoring with Datadog and alerting via Logic Apps
\end{itemize}

\vspace{0.1cm}
\textbf{Data Engineer} \hfill \textbf{Jan 2024 - May 2024}\\
{\color{accentgreen}PRAXAIRLINDE} | Remote
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Developed ETL/ELT workflows with Microsoft Fabric and Databricks
\item Implemented data partitioning and caching strategies in Delta Lake
\item Managed pipeline triggers, parameters, and scheduling with Airflow
\end{itemize}

\vspace{0.1cm}
\textbf{Data Engineer} \hfill \textbf{Aug 2023 - Jan 2024}\\
{\color{accentgreen}TCS (TATA Consultancy Services)} | Guadalajara, Mexico
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Automated CI/CD deployments via Azure DevOps, GitHub Actions, and Terraform
\item Conducted data profiling and validation using Great Expectations and PySpark
\item Optimized data transformation jobs using Python, SQL, and Spark SQL
\end{itemize}

\vspace{0.1cm}
\textbf{Data Engineer} \hfill \textbf{Jan 2022 - Jul 2023}\\
{\color{accentgreen}Grupo Salinas (Elektra EKT)} | Mexico City
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Developed stream-processing apps with Azure Event Hubs and Stream Analytics
\item Designed Azure Synapse Analytics schemas; implemented GDPR-compliant anonymization
\item Built real-time inventory tracking pipelines with Azure Functions
\end{itemize}

\vspace{0.1cm}
\textbf{Data Engineer} \hfill \textbf{Feb 2017 - Dec 2021}\\
{\color{accentgreen}Dealership Performance 360} | Remote
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Ingested data using AWS Glue, Amazon EMR, and Redshift Spectrum
\item Developed Amazon MSK connectors, Kafka, and Elasticsearch integrations
\item Built microservices in Scala on Kubernetes; automated pipelines with Terraform
\end{itemize}""",
        }
