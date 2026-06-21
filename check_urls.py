import os, django, re, pathlib
os.environ['DJANGO_SETTINGS_MODULE'] = 'projet.settings'
os.chdir(r'C:\Users\HP\Desktop\python\projet')
django.setup()
from django.urls import get_resolver
resolver = get_resolver()
url_names = set()
for key, value in resolver.reverse_dict.items():
    if isinstance(key, str):
        url_names.add(key)

tpl_dir = pathlib.Path('candidature/templates/candidature')
for tpl in sorted(tpl_dir.glob('*.html')):
    content = tpl.read_text(encoding='utf-8')
    for m in re.finditer(r"{% url '([^']+)'", content):
        name = m.group(1)
        if name not in url_names:
            print(f'MISSING in {tpl.name}: url "{name}"')

print('Check complete')
