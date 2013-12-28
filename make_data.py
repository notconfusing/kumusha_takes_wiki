# -*- coding: utf-8 -*-
import pywikibot
from pywikibot import pagegenerators
import json
import ast
from collections import defaultdict

en_wikipedia = pywikibot.Site('en', 'wikipedia')
fr_wikipedia = pywikibot.Site('fr', 'wikipedia')
sw_wikipedia = pywikibot.Site('sw', 'wikipedia')
wikidata = en_wikipedia.data_repository()
if not en_wikipedia.logged_in(): en_wikipedia.login()

#this
city_caterogies = {
                   'en': {'all' :'Category:Cities_by_continent', 'ci': 'Category:Populated_places_in_Ivory_Coast', 'ug': 'Category:Populated_places_in_Uganda'},
                   'fr': {'all' :u"Catégorie:Ville_ou_commune_par_continent", 'ci': u"Catégorie:Ville_de_Côte_d'Ivoire", 'ug': u"Catégorie:Ville_d'Ouganda"},
                   'sw': {'all' :u"Jamii:Miji_nchi_kwa_nchi", 'ci': u"Jamii:Miji_ya_Cote_d'Ivoire", 'ug': u"Jamii:Miji_ya_Uganda"}
                   }

city_lists = {
              'en': {'ci': 'List_of_cities_in_Ivory_Coast', 'ug': 'List_of_cities_in_Uganda'},
              'fr': {'ci': u"Liste_des_communes_de_Côte_d'Ivoire_les_plus_peuplées", 'ug': u"Villes_d'Ouganda"},
              'sw': {'ci': u"Orodha_ya_miji_ya_Cote_d'Ivoire", 'ug': u"Orodha_ya_miji_ya_Uganda" }
              }

geography = {
             'en': {'all' :'Category:Geography_by_continent', 'ci': 'Category:Geography_of_Ivory_Coast', 'ug': 'Category:Geography_of_Uganda'},
             'fw': {'all' :u"Catégorie:Géographie par continent", 'ci': u"Catégorie:Géographie_de_la_Côte_d'Ivoire", 'ug': u"Catégorie:Géographie_de_l'Ouganda"},
             'sw':{'all' :u"Jamii:Jiografia_nchi_kwa_nchi", 'ci': u"Jamii:Jiografia_ya_Cote_d'Ivoire", 'ug': u"Jamii:Jiografia_ya_Uganda"}
             }

countries = {
             'en': {'all' :'List_of_countries', 'ci': 'Ivory_Coast', 'ug':'Uganda'},
             'fr': {'all' :u"Liste_des_pays_du_monde", 'ci': u"Côte_d'Ivoire",'ug': u"Ouganda"},
             'sw': {'all' :'Madola', 'ci': u"Cote_d'Ivoire" , 'ug':'Uganda'}
             }

def smartRecurseCat(cat,seen,allpages):
    if list(cat.subcategories()):
        return map(lambda c: smartRecurseCat(c), list(cat.subcategories()))
    else: 
        return set(list(cat.articles()))
        
def categoryeexperiment():
    categoryname = 'Category:Populated_places_by_country'
    #cat = pywikibot.Category(pywikibot.Link(categoryname, defaultNamespace=14))
    cat = pywikibot.Category(en_wikipedia, categoryname)
    pages = pagegenerators.CategorizedPageGenerator(category=cat, recurse=True)
    
    englishpages = set()
    for page in pages:
        if page.namespace() == 0:
            if not page.title().startswith('List of'):
                print page.title()
                englishpages.add(page.title())

    enfile = open('enpages.json','w')
    json.dump(list(englishpages),enfile)
    enfile.close()

def getPagesFromCats(catdict):
    for catlangs in catdict.itrevalues():
        for categoryname in catlangs.itervalues(): 
            pass
        
def findclaim(pid, itemdict):
    claims = itemdict['claims']
    for claimnum, claimlist in claims.iteritems():
        if claimnum == pid:
            return claimlist
    return []
                    


def getCitiesFromWikidata():
    countries = defaultdict(int)
    property_page = pywikibot.ItemPage(wikidata, 'Q515')
    
    pages_with_property = property_page.getReferences(total=100000000)
    
    total = 0
    for page in pages_with_property:
        if page.namespace() == 0:
            total += 1
            itempage = pywikibot.ItemPage(wikidata, page.title())
            page_parts = itempage.get()
            targetclaims = findclaim('P17', page_parts)
            for claim in targetclaims:
                countries[claim.target.title()] += 1
            print total
    with open("countries.json") as f:
        json.dump(countries, f)
    print total