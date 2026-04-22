"""
Serializer — mengubah model Django menjadi JSON untuk API.
"""

from rest_framework import serializers
from .models import Internship, Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "logo_url", "industry", "location"]


class InternshipListSerializer(serializers.ModelSerializer):
    """
    Serializer untuk daftar lowongan — field yang ditampilkan lebih sedikit
    supaya response lebih ringan.
    """
    company = CompanySerializer(read_only=True)
    salary_range = serializers.CharField(read_only=True)
    education_level_display = serializers.CharField(
        source="get_education_level_display",
        read_only=True
    )
    work_type_display = serializers.CharField(
        source="get_work_type_display",
        read_only=True
    )
    source_display = serializers.CharField(
        source="get_source_display",
        read_only=True
    )

    class Meta:
        model = Internship
        fields = [
            "id",
            "title",
            "slug",
            "company",
            "location",
            "work_type",
            "work_type_display",
            "education_level",
            "education_level_display",
            "salary_range",
            "is_salary_visible",
            "source",
            "source_display",
            "source_url",
            "posted_at",
            "deadline",
            "scraped_at",
            "relevant_majors",
            "view_count",
        ]


class InternshipDetailSerializer(InternshipListSerializer):
    """
    Serializer untuk detail lowongan — semua field ditampilkan.
    """
    class Meta(InternshipListSerializer.Meta):
        fields = InternshipListSerializer.Meta.fields + [
            "description",
            "requirements",
            "salary_min",
            "salary_max",
        ]