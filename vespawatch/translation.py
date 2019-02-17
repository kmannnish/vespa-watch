from modeltranslation.translator import register, TranslationOptions
from vespawatch.models import Taxon, IdentificationCard


@register(Taxon)
class SpeciesTranslationOptions(TranslationOptions):
    fields = ('vernacular_name',)

@register(IdentificationCard)
class IdentificationCardTranslationOptions(TranslationOptions):
    fields = ('description',)
