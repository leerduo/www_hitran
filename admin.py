from django.contrib import admin
from hitranlbl.models import OutputCollection

class OutputCollectionAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputCollection, OutputCollectionAdmin)

