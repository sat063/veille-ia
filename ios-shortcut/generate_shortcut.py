#!/usr/bin/env python3
import plistlib,uuid,sys
from pathlib import Path
A=[]
def uid():return str(uuid.uuid4()).upper()
def action(n,**p):
 u=uid();A.append({'WFWorkflowActionIdentifier':'is.workflow.actions.'+n,'WFWorkflowActionParameters':dict(UUID=u,**p)});return u
def V(name):return {'WFSerializationType':'WFTextTokenAttachment','Value':{'Type':'Variable','VariableName':name}}
def O(u,name):return {'WFSerializationType':'WFTextTokenAttachment','Value':{'Type':'ActionOutput','OutputUUID':u,'OutputName':name}}
def T(parts):
 s='';a={}
 for p in parts:
  if isinstance(p,str):s+=p
  else:a['{%d, 1}'%(len(s.encode('utf-16-le'))//2)]=p['Value'];s+='\ufffc'
 return {'WFSerializationType':'WFTextTokenString','Value':{'string':s,'attachmentsByRange':a}}
def setv(n):action('setvariable',WFVariableName=n)
def lit(n,v):action('gettext',WFTextActionText=v);setv(n)
def menu(prompt,items):
 g=uid();action('choosefrommenu',GroupingIdentifier=g,WFControlFlowMode=0,WFMenuItems=items,WFMenuPrompt=prompt);return g
def case(g,n):action('choosefrommenu',GroupingIdentifier=g,WFControlFlowMode=1,WFMenuItemTitle=n)
def end(g):action('choosefrommenu',GroupingIdentifier=g,WFControlFlowMode=2)
def IF(src,cond=100,term=None):
 g=uid();p={'GroupingIdentifier':g,'WFControlFlowMode':0,'WFCondition':cond,'WFInput':{'Type':'Variable','Variable':src}}
 if term is not None:p['WFConditionalActionString']=term
 action('conditional',**p);return g
def END(g):action('conditional',GroupingIdentifier=g,WFControlFlowMode=2)
m=menu('Traduction Photo',['Photographier','Importer','Bloc-notes'])
case(m,'Photographier')
action('takephoto',WFCameraCaptureDevice='Back',WFCameraCaptureShowPreview=False,WFPhotoCount=1);setv('Image')
case(m,'Importer')
action('selectphoto',WFSelectMultiplePhotos=False,WFPhotoPickerTypes=['Images','Live Photos']);setv('Image')
case(m,'Bloc-notes')
f=action('documentpicker.open',WFFileStorageService='iCloud Drive',WFShowFilePicker=True,WFGetFilePath='/Shortcuts/Traduction Photo/',WFFileErrorIfNotFound=False)
action('quicklook',WFInput=O(f,'File'));action('exit')
end(m)
action('extracttextfromimage',WFInput=V('Image'));setv('Original')
g=IF(V('Original'),101);action('showresult',Text='Aucun texte trouve.');action('exit');END(g)
m=menu('Langue cible (francais en premier)',['Francais','Anglais','Espagnol','Allemand','Italien'])
for label,code in [('Francais','fr_FR'),('Anglais','en_US'),('Espagnol','es_ES'),('Allemand','de_DE'),('Italien','it_IT')]:
 case(m,label)
 action('text.translate',WFInputText=V('Original'),WFSelectedFromLanguage='Detect Language',WFSelectedLanguage=code)
 setv('Traduction')
end(m)
lit('Categorie','Divers');lit('Classe','Non')
patterns=[
 ('Alimentation',r'(?i)aliment|ingr.dient|nutrition|calori|recette|lait|friandise|repas|cuisson'),
 ('Factures',r'(?i)factur|payer|paiement|montant|tva|total.t.t|euro|re.u|prix.ttc'),
 ('Animaux',r'(?i)chat|chien|animaux|animal|v.t.rinaire|croquette|liti.re'),
 ('Sante',r'(?i)m.dec|traitement|dosage|m.dicament|laboratoire|sympt.me|ordonnance'),
 ('Voyage',r'(?i)h.tel|a.roport|billet|voyage|r.servation|train|vol\b'),
 ('Travail',r'(?i)contrat|entreprise|r.union|client|employeur|salaire'),
 ('Courrier',r'(?i)cordialement|madame|monsieur|cher.client|lettre|exp.diteur'),
 ('Notice',r'(?i)instruction|utilisation|appareil|avertissement|attention|pr.caution')]
for category,pat in patterns:
 x=action('text.match',WFInput=V('Traduction'),WFMatchTextPattern=pat,WFMatchTextCaseSensitive=False)
 g=IF(O(x,'Matches'))
 h=IF(V('Classe'),4,'Non')
 lit('Categorie',category);lit('Classe','Oui')
 END(h);END(g)
action('file.createfolder',WFFileStorageService='iCloud Drive',WFFilePath=T(['/Shortcuts/Traduction Photo/',V('Categorie'),'/']))
d=action('date',WFDateActionMode='Current Date')
dd=action('format.date',WFDate=O(d,'Date'),WFDateFormatStyle='Custom',WFDateFormat='Custom',WFDateFormatString='yyyy-MM-dd_HH-mm-ss',WFTimeFormatStyle='None')
action('documentpicker.save',WFFileStorageService='iCloud Drive',WFAskWhereToSave=False,WFSaveFileOverwrite=False,WFFileDestinationPath=T(['/Shortcuts/Traduction Photo/',V('Categorie'),'/',O(dd,'Formatted Date'),'.txt']),WFInput=V('Traduction'))
action('setclipboard',WFInput=V('Traduction'),WFLocalOnly=True)
action('showresult',Text=T(['Traduction enregistree : ',V('Categorie'),'\n\n',V('Traduction')]))
workflow={'WFWorkflowActions':A,'WFWorkflowClientVersion':'2700.0.4','WFWorkflowClientRelease':'2700.0.4','WFWorkflowName':'Traduction Photo','WFWorkflowIcon':{'WFWorkflowIconGlyphNumber':59511,'WFWorkflowIconStartColor':463140863},'WFWorkflowTypes':[],'WFWorkflowImportQuestions':[],'WFWorkflowInputContentItemClasses':[],'WFWorkflowOutputContentItemClasses':[],'WFWorkflowHasOutputFallback':False,'WFWorkflowHasShortcutInputVariables':False}
path=Path(sys.argv[1] if len(sys.argv)>1 else 'Traduction_Photo_unsigned.shortcut')
path.parent.mkdir(parents=True,exist_ok=True)
with open(path,'wb') as f:plistlib.dump(workflow,f,fmt=plistlib.FMT_XML,sort_keys=False)
assert len({x['WFWorkflowActionParameters']['UUID'] for x in A})==len(A)
print('Actions:',len(A),'bytes:',path.stat().st_size)
