import os
import tempfile
from backend.services.report_generator import ReportGenerator
from backend.analysis.pipeline import pipeline
from backend.schemas.api_schemas import NormalizedComment
from tests.mock_data import MOCK_COMMENTS_TEXT


def test_all_report_formats():
    normalized = [
        NormalizedComment(id=f"c_{i}", platform="ecommerce", source="upload", text=text, rating=4.0)
        for i, text in enumerate(MOCK_COMMENTS_TEXT)
    ]
    analysis = pipeline.process_comments(normalized, title="Report Test Run", platform="ecommerce")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. PDF
        pdf_path = os.path.join(tmpdir, "report.pdf")
        ReportGenerator.generate_pdf(analysis, pdf_path)
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000

        # 2. HTML
        html_str = ReportGenerator.generate_html(analysis)
        assert "<!DOCTYPE html>" in html_str
        assert "SocialPlus.ai Intelligence Report" in html_str

        # 3. CSV
        csv_str = ReportGenerator.generate_csv(analysis)
        assert "Comment Text" in csv_str
        assert len(csv_str.splitlines()) > 5

        # 4. Excel
        xlsx_path = os.path.join(tmpdir, "report.xlsx")
        ReportGenerator.generate_excel(analysis, xlsx_path)
        assert os.path.exists(xlsx_path)
        assert os.path.getsize(xlsx_path) > 1000

