from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.deconstruct import deconstructible
from django.utils.html import format_html


@deconstructible
class RangeFormatValidator:
    def __call__(self, value):
        invalid_ranges = []
        valid_example = (
            "up to 25 |  | 24 <br>"
            "25 to 150 | 25 | 149 <br>"
            "150 to 300 | 150 | 299 <br>"
            "300 or more | 300 |"
        )

        for range_line in map(str.strip, value.split("\n")):
            if not range_line:
                continue

            parts = range_line.split("|")
            if len(parts) != 3:
                invalid_ranges.append(range_line)
                continue

            label, min_value, max_value = map(str.strip, parts)

            if (
                not label
                or (min_value and not min_value.isdigit())
                or (max_value and not max_value.isdigit())
            ):
                invalid_ranges.append(range_line)

        if invalid_ranges:
            error_message = _(
                "Invalid range format in the following lines: <br><br>"
            ) + "<br>".join(invalid_ranges)
            error_message += _(
                "<br><br>The correct format is: <br> label | from | to <br>"
            )
            error_message += (
                _("<br>For example, this would be a valid list of ranges:<br>")
                + valid_example
            )
            raise ValidationError(format_html(error_message))
