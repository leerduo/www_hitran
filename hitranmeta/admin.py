from django.contrib import admin
from HITRAN.hitranmeta.models import Ref, OutputField, OutputCollection,\
                                     Source, NucSpins, OutputFieldOrder,\
                                     Iso, RefsMap

class IsoAdmin(admin.ModelAdmin):
    pass
admin.site.register(Iso, IsoAdmin)

class RefAdmin(admin.ModelAdmin):
    ordering = ['id','refID']
    search_fields = ['authors', 'title']
admin.site.register(Ref, RefAdmin)

class RefsMapAdmin(admin.ModelAdmin):
    ordering = ['id','refID']
admin.site.register(RefsMap, RefsMapAdmin)

class OutputFieldAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputField, OutputFieldAdmin)

class OutputCollectionAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputCollection, OutputCollectionAdmin)

class OutputFieldOrderAdmin(admin.ModelAdmin):
    pass
admin.site.register(OutputFieldOrder, OutputFieldOrderAdmin)

##################

class SourceAdmin(admin.ModelAdmin):
    list_display = ('id', '__unicode__')
    ordering = ['id',]
    search_fields = ['authors', 'title']
admin.site.register(Source, SourceAdmin)

class NucSpinsAdmin(admin.ModelAdmin):
    pass
admin.site.register(NucSpins, NucSpinsAdmin)
    


