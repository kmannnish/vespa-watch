from modeltranslation.translator import register, TranslationOptions
from vespawatch.models import Taxon

@register(Taxon)
class SpeciesTranslationOptions(TranslationOptions):
    fields = ('vernacular_name',)