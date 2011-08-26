from django.contrib import admin
from HITRAN.hitranmeta.models import Ref, OutputField, OutputCollection

class RefAdmin(admin.ModelAdmin):
    ordering = ['refID']
    pass
admin.site.register(Ref, RefAdmin)

class OutputFieldAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputField, OutputFieldAdmin)

class OutputCollectionAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputCollection, OutputCollectionAdmin)



