import pytest
from pdf_escolar.page_ranges import format_page_ranges, parse_page_ranges


def test_single_pages_and_ranges_keep_entered_order():
    assert parse_page_ranges("3, 1-2, 5", 8) == [2, 0, 1, 4]


def test_open_ended_ranges():
    assert parse_page_ranges("-3, 7-", 8) == [0, 1, 2, 6, 7]


def test_spaces_are_accepted():
    assert parse_page_ranges(" 1 - 2 , 4 ", 5) == [0, 1, 3]


@pytest.mark.parametrize("spec", ["", " ", "1-3,,5", "1,12", "8-3", "0", "1--2"])
def test_invalid_ranges_are_rejected(spec):
    with pytest.raises(ValueError):
        parse_page_ranges(spec, 10)


def test_empty_document_is_rejected():
    with pytest.raises(ValueError):
        parse_page_ranges("1", 0)


def test_format_ranges_compacts_adjacent_pages():
    assert format_page_ranges([1, 2, 3, 7, 9, 10]) == "1-3, 7, 9-10"


def test_format_ranges_deduplicates_and_sorts():
    assert format_page_ranges([4, 2, 3, 3, 2]) == "2-4"


def test_format_empty_selection():
    assert format_page_ranges([]) == ""
