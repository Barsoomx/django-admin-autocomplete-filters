from __future__ import annotations

from typing import Any

from django.contrib.admin.views.autocomplete import AutocompleteJsonView as Base
from django.http import JsonResponse


class AutocompleteJsonView(Base):
    """Overriding django admin's AutocompleteJsonView"""

    model_admin: Any | None = None

    @staticmethod
    def display_text(obj: Any) -> str:
        """
        Hook to specify means for converting object to string for endpoint.
        """
        return str(obj)

    def get(self, request: Any, *args: Any, **kwargs: Any) -> JsonResponse:
        if not hasattr(self, 'model_admin') and hasattr(self, 'process_request'):
            self.term, self.model_admin, self.source_field, _ = self.process_request(request)
        else:
            self.term = request.GET.get('term', '')
        assert self.model_admin is not None
        self.paginator_class = self.model_admin.paginator
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse(
            {
                'results': [{'id': str(obj.pk), 'text': self.display_text(obj)} for obj in context['object_list']],
                'pagination': {'more': context['page_obj'].has_next()},
            },
        )

    def get_queryset(self) -> Any:
        """Return queryset based on ModelAdmin.get_search_results()."""
        assert self.model_admin is not None
        qs = self.model_admin.get_queryset(self.request)
        if hasattr(self.source_field, 'get_limit_choices_to'):
            qs = qs.complex_filter(self.source_field.get_limit_choices_to())
        qs, search_use_distinct = self.model_admin.get_search_results(self.request, qs, self.term)
        if search_use_distinct:
            qs = qs.distinct()
        return qs
