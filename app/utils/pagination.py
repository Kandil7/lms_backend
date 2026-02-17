from dataclasses import dataclass


@dataclass(slots=True)
class PageParams:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(items: list, total: int, params: PageParams) -> dict:
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
    }
