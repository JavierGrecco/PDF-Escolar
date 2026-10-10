"""Spanish, user-friendly messages for common PDF failures."""
from pdf_escolar.ui.messages import friendly_export_error, friendly_pdf_load_error


def test_password_protection_has_a_clear_spanish_message():
    message = friendly_pdf_load_error("password required")

    assert "contraseña" in message.lower()
    assert "password" not in message.lower()


def test_permission_errors_do_not_expose_technical_details():
    message = friendly_pdf_load_error("Permission denied: [Errno 13]")

    assert "permiso" in message.lower()
    assert "errno" not in message.lower()
    assert "permission" not in message.lower()


def test_damaged_pdf_gets_a_human_explanation():
    message = friendly_pdf_load_error("invalid PDF structure")

    assert "dañado" in message.lower() or "válido" in message.lower()
    assert "invalid pdf" not in message.lower()


def test_unknown_pdf_error_does_not_echo_library_text():
    internal_detail = "stream ended unexpectedly at object offset 54321"
    message = friendly_pdf_load_error(internal_detail)

    assert "no pudimos abrir" in message.lower()
    assert internal_detail not in message


def test_disk_full_error_suggests_a_simple_next_step():
    message = friendly_export_error("No space left on device")

    assert "espacio" in message.lower()
    assert "liberá" in message.lower() or "otra carpeta" in message.lower()
    assert "no space left" not in message.lower()


def test_export_permission_error_is_friendly_and_reassuring():
    message = friendly_export_error("Permission denied: output.pdf")

    assert "permiso" in message.lower()
    assert "otra carpeta" in message.lower()
    assert "permission denied" not in message.lower()
