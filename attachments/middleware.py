from functools import cmp_to_key

from django.utils.deprecation import MiddlewareMixin


def cmp(a, b):
    # cmp() is removed in python 3
    # https://docs.python.org/3.0/whatsnew/3.0.html#ordering-comparisons
    return (a > b) - (a < b)


def parse_accept_header(accept):
    """Parse the Accept header *accept*, returning a list with pairs of
    (media_type, q_value), ordered by q values.
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0)
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(key=cmp_to_key(lambda x, y: -cmp(x[2], y[2])))
    return result


class AcceptMiddleware(MiddlewareMixin):
    def process_request(self, request):
        accept = parse_accept_header(request.META.get("HTTP_ACCEPT", ""))
        request.accept = accept

        def mapper(toople):
            t, p, q = toople
            return t
        request.accepted_types = list(map(mapper, accept))
