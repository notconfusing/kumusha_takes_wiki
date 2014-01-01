# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>



import pywikibot
import mwparserfromhell as pfh


def readable_text_length(wikicode):
    #could also use wikicode.filter_text()
    return float(len(wikicode.strip_code()))

def infonoise(wikicode):
    wikicode.strip_code()
    ratio = readable_text_length(wikicode) / float(len(wikicode))
    return ratio

# <markdowncell>

# Helper function to mine for section headings, of course if there is a lead it doesn't quite make sense.

# <codecell>

def section_headings(wikicode):
    sections = wikicode.get_sections()
    sec_headings = map( lambda s: filter( lambda l: l != '=', s), map(lambda a: a.split(sep='\n', maxsplit=1)[0], sections))
    return sec_headings

# <markdowncell>

# Metric of article references

# <codecell>

#i don't know why mwparserfromhell's .fitler_tags() isn't working at the moment. going to hack it for now
import re
def num_refs(wikicode):
    text = str(wikicode)
    reftags = re.findall('<(\ )*?ref', text)
    return len(reftags)

def article_refs(wikicode):
    sections = wikicode.get_sections()
    return float(reduce( lambda a,b: a+b ,map(num_refs, sections)))

# <markdowncell>

# Predicate for links and files in English French and Swahili

# <codecell>

def link_a_file(linkstr):
    fnames = [u'File:', u'Fichier:', u'Image:', u'Picha:']
    bracknames = map(lambda a: '[[' + a, fnames)
    return any(map(lambda b: linkstr.startswith(b), bracknames))

def link_a_cat(linkstr):
    cnames =[u'Category:', u'Catégorie:', u'Jamii:']
    bracknames = map(lambda a: '[[' + a, cnames)
    return any(map(lambda b: linkstr.startswith(b), bracknames))

def num_reg_links(wikicode):
    reg_links = filter(lambda a: not link_a_file(a) and not link_a_cat(a), wikicode.filter_wikilinks())
    return float(len(reg_links))

def num_file_links(wikicode):
    file_links = filter(lambda a: link_a_file(a), wikicode.filter_wikilinks())
    return float(len(file_links))

# <markdowncell>

# Metric to determine empty secs sections ala Maik et al en ''Predicting Quality Flaws in User Generated Content (2012)''

# <codecell>

def short_sections(wikicode, thresh=20):
    """returns the number of sections shorter than 20"""
    sections = wikicode.get_sections()
    return reduce( lambda a,b: a+b, map( lambda s: len(s)<= thresh, sections))
    

# <headingcell level=2>

# The Metric Maker that is called on Wikicode

# <codecell>

def report_actionable_metrics(wikicode, completeness_weight=0.8, infonoise_weight=0.6, images_weight=0.3):
    '''following the guidelines of the "Tell me more" paper'''
    completeness = completeness_weight * num_reg_links(wikicode)
    informativeness = (infonoise_weight * infonoise(wikicode) ) + (images_weight * num_file_links(wikicode) )
    numheadings = len(section_headings(wikicode))
    articlelength = readable_text_length(wikicode)
    referencerate = article_refs(wikicode) / readable_text_length(wikicode)
    
    return {'completeness': completeness, 'informativeness': informativeness, 'numheadings': numheadings, 'articlelength': articlelength, 'referencerate': referencerate} 

# <headingcell level=3>

# Testing the Metric Maker on the Article About the UK

# <codecell>

enwp = pywikibot.Site('en','wikipedia')
testpage = pywikibot.Page(enwp, 'United_Kingdom')
testtext = testpage.get()
wikicode = pfh.parse(testtext)

# <codecell>

report_actionable_metrics(wikicode)

# <headingcell level=2>

# Getting the Wikidata item for every country

# <markdowncell>

# Mining these from English Wikipedia List of Countries by Popultation. I did mine them also from Wikidata items from an offline parsing using "isntance of" "country". But got only 133 items For the offline parser see <https://github.com/mkroetzsch/wda>

# <codecell>

import os
import datetime
import json
from collections import defaultdict

# <codecell>

langs = ['en','fr','sw']

wikipedias = {lang: pywikibot.Site(lang, 'wikipedia') for lang in langs}
wikidata = wikipedias['fr'].data_repository()

# <markdowncell>

# this will be our data structure dict of dicts, until we have some numbers to put into pandas

# <codecell>

def enfrsw():
    return {lang: None for lang in langs}
def article_attributes():
    return {attrib: enfrsw() for attrib in ['sitelinks', 'wikitext', 'wikicode', 'metrics']}

# <codecell>

def do_sitelinks(langs, qids, data):
    for qid in qids:
        page = pywikibot.ItemPage(wikidata, qid)
        wditem = page.get()
        for lang in langs:
            try:
                data[qid]['sitelinks'][lang] = wditem['sitelinks'][lang+'wiki']
            except KeyError:
                pass
    return data

# <markdowncell>

# and then then functions to get the page texts in all our desired languages

# <codecell>

def get_wikitext(lang, title):
    page = pywikibot.Page(wikipedias[lang],title)
    def get_page(page):
        try:
            pagetext = page.get()
            return pagetext
        except pywikibot.exceptions.IsRedirectPage:
            redir = page.getRedirectTarget()
            get_page(redir)
        except pywikibot.exceptions.NoPage:
            raise pywikibot.exceptions.NoPage
            print 're raising'
    return get_page(page)

def do_wikitext(langs, data):
    for qid, attribs in data.iteritems():
        for lang, sl in attribs['sitelinks'].iteritems():
            if sl:
                try:
                    if randint(0,100) == 99:
                        print sl
                    data[qid]['wikitext'][lang] = get_wikitext(lang, sl)
                except:
                    print 'bad sitelink', sl
                    continue
    return data

# <codecell>

def do_wikicode(langs, data):
    for qid, attribs in data.iteritems():
        for lang, pagetext in attribs['wikitext'].iteritems():
            if pagetext:
                data[qid]['wikicode'][lang] = pfh.parse(pagetext)
    return data

# <markdowncell>

# calculate our metrics from above

# <codecell>

def do_metrics(data):
    for qid, attribs in data.iteritems():
        for lang, wikicode in attribs['wikicode'].iteritems():
            if wikicode:
                data[qid]['metrics'][lang] = report_actionable_metrics(wikicode)
    return data

# <markdowncell>

# this will take a lot of network time since we are going to load about 300 pages, but we'll save the data off so we don't have to do it uneccesarrily

# <codecell>

def make_data(langs, qids, savename):
    print 'getting these qids: ', qids 
    data = defaultdict(article_attributes)
    print 'getting sitelinks'
    data = do_sitelinks(langs, qids, data)
    print 'getting wikitext'
    data = do_wikitext(langs, data)
    print 'converting to wikicode'
    data = do_wikicode(langs, data)
    print 'computing metrics'
    data = do_metrics(data)

        
    hashable_data = {qid: 
                        {'wikitext': attribdict['wikitext'],
                         'metrics': attribdict['metrics'],
                         'sitelinks': attribdict['sitelinks']}
                             for qid, attribdict in data.iteritems()}
    print 'saving now'
    #save the results
    safefilename = savename+str(datetime.datetime.now())+'.json'
    with open(safefilename,'w') as f3:
        json.dump(hashable_data,f3)
    with open(savename+'latest.json','w') as f4:
        json.dump(hashable_data, f4)
    return data



print make_data(langs, ['Q7857683'], 'testfilename')

# <codecell>

from os import listdir

ethnofiles = listdir('ethnosets')
for ethnofile in ethnofiles:
    nameparts = ethnofile.split('-') 
    print nameparts
    subj = nameparts[0]
    nation = nameparts[1].replace('.json','')
    activefile = open('ethnosets/'+ethnofile, 'r')
    activeqids = json.load(activefile)
    print 'making data on', ethnofile
    make_data(langs, activeqids, ethnofile)


# <codecell>


