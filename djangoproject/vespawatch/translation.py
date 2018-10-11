from modeltranslation.translator import register, TranslationOptions
from vespawatch.models import Species

@register(Species)
class SpeciesTranslationOptions(TranslationOptions):
    fields = ('vernacular_name',)