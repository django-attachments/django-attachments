from functools import cmp_to_key


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


class AcceptMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        accept = parse_accept_header(request.META.get("HTTP_ACCEPT", ""))
        request.accept = accept

        def mapper(toople):
            t, p, q = toople
            return t
        request.accepted_types = list(map(mapper, accept))
        response = self.get_response(request)
        return response
