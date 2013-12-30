# -*- coding: utf-8 -*-
import pywikibot
from pywikibot import pagegenerators
import json
import ast
from collections import defaultdict

langs = ['en','fr','sw']
wikipedias = {lang: pywikibot.Site(lang, 'wikipedia') for lang in langs}

wikidata = wikipedias['fr'].data_repository()
if not wikipedias['en'].logged_in(): wikipedias['en'].login()

class category_inspection():
    def __init__(self):
        #these are the data that we'll be operating on
        self.base_categories = list()
        self.seen_categories = list()
        #a list of pywikibot.Page's
        self.accepted_articles = list()
        self.seen_articles = list()
        #list of qids
        self.qids = set()
        
    def uniqueify_cats(self):
        before = len(self.base_categories)
        self.base_categories = list(set(self.base_categories))
        print lang + ': slimmed from ' + str(before) + 'cats to ' + str(len(self.base_categories))

    def uniqueify_arts(self):
        before = len(self.accepted_articles)
        self.accepted_articles = list(set(self.accepted_articles))
        print 'slimmed from ' + str(before) + 'articles to ' + str(len(self.accepted_articles))


def choose_from_list(ci,get_arts=False,get_subcats=False):
    '''should be used XOR get_arts or get_subcats, both of which are a category'''
    if get_subcats:
        geny = pagegenerators.SubCategoriesPageGenerator(category=get_subcats, recurse=False)
        gen = list(geny)
        seen = ci.seen_categories
        seen.append(get_subcats)
        savelist = ci.base_categories
    
    if get_arts:
        gen = list(get_arts.articles())
        seen = ci.seen_articles
        seen.append(get_arts)
        savelist = ci.accepted_articles

        
    try:
        unseen_gen = filter(lambda o: o not in seen, gen)
        if len(unseen_gen) == 0:
            return
        gen_numbered = zip(range(1, len(gen)+1 ),  unseen_gen)
        #print out out the list 
        for tup in gen_numbered:
            print tup[0], tup[1]
            
        #get input
        want = raw_input('which numbers, comma separated ("a" all or "n" negate then numbers)')
        #see if we are taking anything
        if want:
            #see if we are accepting all
            if want == 'a':
                savelist.extend(unseen_gen)
                seen.extend(unseen_gen)
                if get_subcats:
                    for subsubcat in unseen_gen:
                        choose_from_list(ci, get_subcats=subsubcat)
                return
            
            negate = False
            if want.startswith('n'):
                negate = True
                want = want[1:] 
                
            want = map(lambda a: int(a), want.split(','))
            will_have_tups = filter(lambda tup: in_or_out(negate, tup[0], want), gen_numbered)
            will_have = map(lambda tup: tup[1], will_have_tups)
            savelist.extend(will_have)
            seen.extend(unseen_gen)
            if get_subcats:
                for subsubcat in will_have:
                    choose_from_list(ci, get_subcats=subsubcat)
            return
    except ValueError:
        print 'bad entry try again'
        choose_from_list(ci, get_arts=get_arts, get_subcats=get_subcats)
    


def in_or_out(negate, num, want):
    if negate:
        return num not in want
    else:
        return num in want
        

def make_base_categories(ci, predefined=False):
    seen = set()
    if not predefined:
        def get_inp(lang):
            inp = raw_input(lang + " : Enter a base category to search. Empty input to continue")
            if inp:
                ci.base_categories.append(pywikibot.Category(wikipedias[lang], inp))
                get_inp(lang)
            if not inp:
                return
            
        for lang in langs:
            get_inp(lang)
    else:
        for lang, inp in predefined.iteritems():
            ci.base_categories.append(pywikibot.Category(wikipedias[lang], inp))

        
    print 'we got these categories'
    print ci.base_categories
    inp = raw_input('shall we look into their subcategories?')
    if inp:
        def all_subcats(cat):
            try:
                subcats = pagegenerators.SubCategoriesPageGenerator(category=cat, recurse=False)
                scl = list(subcats)
                if len(scl) == 0:
                    return
                scl_numbered = zip(range(1,len(scl)+1),  scl)
                scul = map(lambda tit: u'https://' +lang+ u'.wikipedia.org/wiki/'+ tit.title(asLink=True),scl)
                scul_numbered = zip(range(1,len(scul)+1),  scul)
                #its difficult to read french urls with diacritics
                for tup in scl_numbered:
                    print tup[0], tup[1]
                want = raw_input('which numbers do you want, comma separated (a all or n negate)')
                if want:
                    if want == 'a':
                        ci.base_categories[lang].extend(scl)
                        return
                    
                    negate = False
                    if want.startswith('n'):
                        negate = True
                        want = want[1:] 
                        
                    want = map(lambda a: int(a), want.split(','))
                    will_have_tups = filter(lambda tup: in_or_out(negate, tup[0], want), scl_numbered)
                    will_have = map(lambda tup: tup[1], will_have_tups)
                    ci.base_categories[lang].extend(will_have)
                    for subsubcat in will_have:
                        if not subsubcat in seen:
                            seen.add(subsubcat)
                            all_subcats(subsubcat)
            except ValueError:
                print 'bad entry try again'
                all_subcats(cat)
                
                
        print 'processing subcats'
        for lang, catlist in ci.base_categories.iteritems():
            print 'working on ' + lang
            for cat in catlist:
                if not cat in seen:
                    print 'starting from', cat
                    seen.add(cat)
                    all_subcats(cat)
            
    print 'final list:'
    ci.uniqueify_cats()
    print ci.base_categories

def inspect_articles(ci):
    for lang, categories in ci.base_categories.iteritems():
        for category in categories:
                al = list(category.articles())
                if not al:
                    continue
                aul = map(lambda tit: 'https://'+lang+'.wikipedia.org/wiki/'+tit.title(asUrl=True),al)
                aul_numbered = zip(range(1,len(aul)+1),  aul)
                al_numbered = zip(range(1,len(al)+1),  al)
                for tup in al_numbered:
                    print tup[0], tup[1]
                want = raw_input('which numbers do you want, comma separated, (a for all, n to negate)')
                if want:
                    if want == 'a':
                        ci.accepted_articles.extend(al)
                        continue
                    
                    negate = False
                    if want.startswith('n'):
                        negate = True
                        want = want[1:]    
                                    
                    want = map(lambda a: int(a), want.split(','))

                    will_have_tups = filter(lambda tup: in_or_out(negate, tup[0], want), al_numbered)
                    will_have = map(lambda tup: tup[1], will_have_tups)
                    print will_have
                    ci.accepted_articles.extend(will_have)
    
    print 'final list:'
    ci.uniqueify_arts()
    print ci.accepted_articles
            

def make_qids(ci): 
    for art in ci.accepted_articles:
        try:
            artitem = pywikibot.ItemPage.fromPage(art)
            artqid = artitem.title()
            ci.qids.add(artqid)
        except:
            print 'trouble getting wikidata on', art
            continue
        
def save(ci,subject,country):
    filename = subject + '-' + country + '.json'
    f = open('./ethnosets/' + filename, 'w')
    json.dump(list(ci.qids), f)
    print 'saved'
    
if __name__ == '__main__':
    def test():
        ci = category_inspection()
        for cat in [pywikibot.Category(wikipedias['en'],'Category:Allah') , pywikibot.Category(wikipedias['en'],'Category:God'), pywikibot.Category(wikipedias['fr'],'Catégorie:Dieu')]:
            choose_from_list(ci,get_subcats=cat)
        print ci.base_categories
    
    startcats = json.load(open('ethnosets-categories.json', 'r'))
    for subject, countrydict in startcats.iteritems():
        for country, langdict in countrydict.iteritems():
            print 'this is:' + str(subject) +' of ' + str(country)
            r = raw_input('do you want to do this one? y/n')
            if r == 'y':
                ci = category_inspection()
                make_base_categories(ci, predefined=langdict)
                inspect_articles(ci)
                make_qids(ci)
                save(ci,subject,country)
            