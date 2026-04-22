from django.contrib import admin
from .models import Company, Internship, ScrapingLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "industry", "location", "created_at"]
    search_fields = ["name", "industry"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "source", "status", "posted_at", "deadline"]
    list_filter = ["status", "source", "work_type", "education_level"]
    search_fields = ["title", "company__name", "location"]
    readonly_fields = ["scraped_at", "created_at", "updated_at", "view_count"]
    prepopulated_fields = {"slug": ["title"]}

    # Tambahkan action untuk approve/reject lowongan massal
    actions = ["approve_internships", "reject_internships"]

    @admin.action(description="Setujui lowongan terpilih")
    def approve_internships(self, request, queryset):
        updated = queryset.update(status=Internship.Status.ACTIVE)
        self.message_user(request, f"{updated} lowongan berhasil disetujui.")

    @admin.action(description="Tolak lowongan terpilih")
    def reject_internships(self, request, queryset):
        updated = queryset.update(status=Internship.Status.REJECTED)
        self.message_user(request, f"{updated} lowongan berhasil ditolak.")


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ["source", "status", "total_found", "total_saved", "started_at"]
    list_filter = ["source", "status"]
    readonly_fields = ["started_at", "finished_at"]