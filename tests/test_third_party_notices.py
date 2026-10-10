"""Tests for user-accessible third-party license notices."""

from pdf_escolar.third_party_notices import load_third_party_notices


def test_source_tree_provides_a_clear_license_notice_template():
    notices = load_third_party_notices()

    assert notices.strip()
    assert "inventario completo se genera durante la compilación" in notices
    assert "no sustituye la revisión manual" in notices
