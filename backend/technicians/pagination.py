from rest_framework.pagination import PageNumberPagination

class NinePerPagePagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"  # optional override
    max_page_size = 50
