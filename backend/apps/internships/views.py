"""
API Views untuk lowongan magang.
Menggunakan Django REST Framework untuk expose data ke frontend Next.js.
"""

import logging
from django.db.models import Q
from rest_framework import generics, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Internship
from .serializers import InternshipListSerializer, InternshipDetailSerializer

logger = logging.getLogger(__name__)


class InternshipPagination(PageNumberPagination):
    """
    Pagination — membagi hasil menjadi halaman-halaman.
    Default 20 per halaman, maksimal 100.
    """
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class InternshipListView(generics.ListAPIView):
    """
    GET /api/internships/
    Ambil daftar lowongan dengan filter dan search.

    Query params yang didukung:
    - search       : cari di judul dan nama perusahaan
    - source       : filter by sumber (glints/indeed)
    - work_type    : filter by tipe kerja (onsite/remote/hybrid)
    - education    : filter by jenjang (d3/d4/s1/all/unknown)
    - location     : filter by kota (partial match)
    - page         : nomor halaman
    - page_size    : jumlah item per halaman (default 20, max 100)
    """
    serializer_class = InternshipListSerializer
    pagination_class = InternshipPagination

    def get_queryset(self):
        # Hanya tampilkan lowongan yang statusnya ACTIVE atau PENDING
        # PENDING = baru di-scrape, belum diverifikasi — tetap ditampilkan untuk MVP
        queryset = Internship.objects.filter(
            status__in=[Internship.Status.ACTIVE, Internship.Status.PENDING]
        ).select_related("company").order_by("-scraped_at")

        # --- Filter: search keyword ---
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(company__name__icontains=search) |
                Q(location__icontains=search)
            )

        # --- Filter: sumber ---
        source = self.request.query_params.get("source", "").strip()
        if source in ["glints", "indeed"]:
            queryset = queryset.filter(source=source)

        # --- Filter: tipe kerja ---
        work_type = self.request.query_params.get("work_type", "").strip()
        if work_type in ["onsite", "remote", "hybrid"]:
            queryset = queryset.filter(work_type=work_type)

        # --- Filter: jenjang pendidikan ---
        education = self.request.query_params.get("education", "").strip()
        if education in ["d3", "d4", "s1", "all"]:
            if education == "d3":
                # Tampilkan D3 + "semua jenjang" + unknown
                # (unknown kemungkinan besar menerima D3 juga)
                queryset = queryset.filter(
                    Q(education_level=Internship.EducationLevel.D3) |
                    Q(education_level=Internship.EducationLevel.ALL) |
                    Q(education_level=Internship.EducationLevel.UNKNOWN)
                )
            else:
                queryset = queryset.filter(education_level=education)

        # --- Filter: lokasi ---
        location = self.request.query_params.get("location", "").strip()
        if location:
            queryset = queryset.filter(location__icontains=location)

        return queryset


class InternshipDetailView(generics.RetrieveAPIView):
    """
    GET /api/internships/<slug>/
    Ambil detail satu lowongan berdasarkan slug.
    Sekaligus tambah view_count.
    """
    serializer_class = InternshipDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Internship.objects.filter(
            status__in=[Internship.Status.ACTIVE, Internship.Status.PENDING]
        ).select_related("company")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Tambah view count setiap kali detail dibuka
        Internship.objects.filter(pk=instance.pk).update(
            view_count=instance.view_count + 1
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@api_view(["GET"])
def api_stats(request):
    """
    GET /api/stats/
    Statistik ringkas untuk ditampilkan di dashboard frontend.
    """
    total = Internship.objects.filter(
        status__in=[Internship.Status.ACTIVE, Internship.Status.PENDING]
    ).count()

    by_source = {
        "glints": Internship.objects.filter(source="glints").count(),
        "indeed": Internship.objects.filter(source="indeed").count(),
    }

    by_work_type = {
        "onsite": Internship.objects.filter(work_type="onsite").count(),
        "remote": Internship.objects.filter(work_type="remote").count(),
        "hybrid": Internship.objects.filter(work_type="hybrid").count(),
        "unknown": Internship.objects.filter(work_type="unknown").count(),
    }

    return Response({
        "total_internships": total,
        "by_source": by_source,
        "by_work_type": by_work_type,
    })