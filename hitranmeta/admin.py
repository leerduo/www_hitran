from django.contrib import admin
from HITRAN.hitranmeta.models import OutputField, OutputCollection,\
                                     Source, NucSpins, OutputFieldOrder,\
                                     Iso, Molecule, RefsMap, PrmDesc

class MoleculeAdmin(admin.ModelAdmin):
    pass
admin.site.register(Molecule, MoleculeAdmin)

class IsoAdmin(admin.ModelAdmin):
    pass
admin.site.register(Iso, IsoAdmin)

class PrmDescAdmin(admin.ModelAdmin):
    pass
admin.site.register(PrmDesc, PrmDescAdmin)

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
    ordering = ['output_collection', 'position']
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
