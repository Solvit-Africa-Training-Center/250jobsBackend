from rest_framework.pagination import PageNumberPagination

class JobsPagination(PageNumberPagination):
    page_size = 12   # adjust if you prefer 9 everywhere
    page_size_query_param = "page_size"
    max_page_size = 50
