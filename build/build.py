#!/usr/bin/env python3
"""Build the static withdental.kr site from the design canvas pages."""
import json, os, re, shutil, subprocess, html
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'project')
OUT = os.environ.get('WD_OUT', os.path.join(ROOT, '_site'))
BUILD = os.path.dirname(os.path.abspath(__file__))
DOMAIN = 'https://withdental.kr'
BLOBMAP = {k: os.path.join(ROOT, v) for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blobmap.json'))).items()}

PAGES = {
    'Main': dict(path='', lang='ko',
        title='여의도 치과 위드치과보철과 | 보철과·교정과 전문의 진료 (Since 1993)',
        desc='여의도 치과 위드치과보철과. 1993년부터 같은 자리에서 진료해 왔습니다. 치과보철과 전문의와 치과교정과 전문의가 함께 진단하는 앞니 심미보철, 자연치아 보존 수복, 임플란트, 전악보철·교합재건, 인비절라인 교정. 여의도역 4번 출구 도보 1분, 예약제 운영.'),
    'English': dict(path='en/', lang='en',
        title='WITH Dental Clinic Seoul | English-speaking Prosthodontist & Orthodontist in Yeouido',
        desc='Prosthodontic and orthodontic care in English in Yeouido, Seoul, since 1993. 100% by appointment: book by email or KakaoTalk. A 1-minute walk from Yeouido Station, Exit 4.'),
    'Chinese': dict(path='zh/', lang='zh-Hans',
        title='首尔汝矣岛 WITH 牙科 | 口腔修复科·正畸科专科医生诊疗（Since 1993）',
        desc='首尔汝矣岛的 WITH 牙科，自1993年起在同一地点诊疗。口腔修复科与正畸科专科医生协同诊疗。距 The Hyundai Seoul 步行约3分钟，金浦机场乘地铁约15分钟。可提前预约合作的牙科专业中文翻译。100% 预约制。'),
    'ChineseTraditional': dict(path='zh-hant/', lang='zh-Hant',
        title='首爾汝矣島 WITH 牙科 | 口腔修復科·正畸科專科醫生診療（Since 1993）',
        desc='首爾汝矣島的 WITH 牙科，自1993年起在同一地點診療。口腔修復科與正畸科專科醫生協同診療。距 The Hyundai Seoul 步行約3分鐘，金浦機場乘地鐵約15分鐘。可提前預約合作的牙科專業中文翻譯。100% 預約制。'),
    'Notice': dict(path='notice/', lang='ko',
        title='공지사항 · 월별 진료 일정 | 위드치과보철과',
        desc='위드치과보철과의 월별 원장 진료 일정과 휴진 안내 등 공지사항입니다.'),
    'Rights': dict(path='patient-rights/', lang='ko',
        title='환자의 권리와 의무 | 위드치과보철과',
        desc='의료법 시행규칙에 따른 환자의 권리와 의무 안내입니다.'),
    'Privacy': dict(path='privacy/', lang='ko',
        title='개인정보처리방침 | 위드치과보철과',
        desc='위드치과보철과 개인정보처리방침입니다.'),
    'Invisalign': dict(path='treatments/invisalign/', lang='ko',
        title='여의도 인비절라인 투명교정 | 위드치과보철과 (치과교정과 전문의 진료)', crumb='인비절라인 투명교정',
        about=['인비절라인 투명교정', '투명교정', '치아교정'],
        desc='여의도 위드치과보철과의 인비절라인 투명교정. 치과교정과 전문의가 진단부터 유지 관리까지 직접 계획하고, 보철 치료가 필요하면 치과보철과 전문의와 함께 최종 모습을 설계합니다. 착용 시간, 치료 과정, 브라켓 교정과의 비교, 자주 묻는 질문.'),
    'Restorative': dict(path='treatments/conservative-restoration/', lang='ko',
        title='여의도 자연치아 보존 수복 (레진·인레이·온레이·오버레이) | 위드치과보철과', crumb='자연치아 보존 수복',
        about=['자연치아 보존 수복', '레진 수복', '인레이', '온레이', '접착 오버레이', '생체모방 치과치료(Biomimetic)'],
        desc='여의도 위드치과보철과의 자연치아 보존 수복. 충치와 손상 범위에 따라 레진 빌드업, 인레이, 온레이, 오버레이 순으로 가장 적게 깎는 방법을 고르고, 러버댐 격리 하에 접착 기반의 생체모방 치료(Biomimetic)로 진행합니다. 치과보철과 전문의 배민수 원장 진료.'),
    'Esthetic': dict(path='treatments/esthetic-prosthodontics/', lang='ko',
        title='여의도 앞니 심미보철 (라미네이트·크라운·레진 비니어) | 위드치과보철과', crumb='심미보철치료',
        about=['앞니 심미보철', '라미네이트', '크라운', '앞니 크라운 재치료', '레진 비니어', '진단 왁스업·목업'],
        desc='여의도 위드치과보철과의 앞니 심미보철. 옆 치아와 구분되지 않는 자연스러운 앞니를 위해 색과 투명도를 분석하고, 진단 왁스업과 목업으로 결과를 먼저 확인한 뒤 최소 삭제로 라미네이트·크라운·무삭제 레진 비니어를 진행합니다. 앞니 재치료 사례와 자주 묻는 질문. 치과보철과 전문의 배민수 원장 진료.'),
    'Perio': dict(path='treatments/periodontal-plastic-surgery/', lang='ko',
        title='여의도 미세치주성형 (잇몸퇴축 치근피개술·결합조직이식·거미스마일) | 위드치과보철과', crumb='미세치주성형',
        about=['미세치주성형', '치근피개술', '결합조직이식', '잇몸퇴축 치료', '거미스마일 치은성형술'],
        desc='여의도 위드치과보철과의 미세치주성형. 내려간 잇몸을 올려 드러난 뿌리를 덮는 치근피개술과 결합조직이식, 잇몸 두께 재건, 치은성형술로 거미스마일 개선까지. 실제 치료 사례와 자주 묻는 질문.'),
    'Fees': dict(path='fees/', lang='ko', noindex=True,
        title='비급여 진료비 안내 | 위드치과보철과',
        desc='위드치과보철과 비급여 진료비 안내입니다.'),
}

LINKMAP = {k: v['path'] for k, v in PAGES.items()}

JSONLD_CLINIC = {
    "@context": "https://schema.org",
    "@type": "Dentist",
    "@id": DOMAIN + "/#clinic",
    "name": "위드치과보철과",
    "alternateName": ["WITH Dental Clinic Seoul", "위드치과"],
    "url": DOMAIN + "/",
    "logo": DOMAIN + "/assets/img/web-logo.png",
    "image": DOMAIN + "/assets/img/hero1.jpg",
    "description": "1993년부터 여의도에서 진료해 온 치과. 치과보철과 전문의와 치과교정과 전문의가 협진합니다.",
    "foundingDate": "1993",
    "telephone": "+82-2-783-2825",
    "faxNumber": "+82-2-783-2826",
    "email": "withdental_seoul@naver.com",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "여의나루로 53-1 대오빌딩 4층 401호",
        "addressLocality": "영등포구",
        "addressRegion": "서울특별시",
        "addressCountry": "KR"
    },
    "openingHoursSpecification": [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "opens": "10:00", "closes": "18:30"
    }],
    "hasMap": "https://maps.google.com/?q=%EC%84%9C%EC%9A%B8%20%EC%98%81%EB%93%B1%ED%8F%AC%EA%B5%AC%20%EC%97%AC%EC%9D%98%EB%82%98%EB%A3%A8%EB%A1%9C%2053-1",
    "areaServed": ["여의도", "여의도동", "영등포구", "서울"],
    "knowsAbout": ["앞니 심미보철", "라미네이트", "크라운", "레진 비니어", "자연치아 보존 수복", "접착 오버레이", "임플란트", "전악보철", "교합재건", "인비절라인 투명교정", "치아교정", "미세치주성형", "치근피개술"],
    "employee": [
        {"@type": "Person", "name": "배민수", "alternateName": "Minsoo Bae", "jobTitle": "대표원장 · 치과보철과 전문의"},
        {"@type": "Person", "name": "강재연", "alternateName": "Jaeyoen Kang", "jobTitle": "대표원장 · 치과교정과 전문의"}
    ],
    "availableLanguage": ["Korean", "English", "Japanese"],
    "medicalSpecialty": ["Prosthodontic", "Orthodontic", "Periodontic"],
    "sameAs": [
        "https://www.youtube.com/@withdentalseoul",
        "https://pf.kakao.com/_xjeAxmG",
        "https://booking.naver.com/booking/13/bizes/1126036"
    ]
}


def split_dc(src):
    helmet = re.search(r'<helmet>([\s\S]*?)</helmet>', src).group(1)
    body = re.search(r'<x-dc>([\s\S]*)</x-dc>', src).group(1)
    body = re.sub(r'<helmet>[\s\S]*?</helmet>', '', body, count=1).strip()
    m = re.search(r"<script type=\"text/x-dc\" data-dc-script data-props='([^']*)'>([\s\S]*?)</script>", src)
    props_decl = json.loads(m.group(1))
    logic = m.group(2)
    props = {k: v.get('default') for k, v in props_decl.items() if not k.startswith('$') and isinstance(v, dict)}
    return helmet, body, logic, props


def rewrite(text, prefix, img_names):
    # cross-page links
    def link(m):
        page, frag = m.group(1), m.group(2) or ''
        target = LINKMAP.get(page)
        if target is None:
            return m.group(0)
        url = prefix + target if (prefix + target) else './'
        return 'href="%s%s"' % (url, frag)
    text = re.sub(r'href="([A-Za-z]+)\.dc\.html(#[^"]*)?"', link, text)
    # uploaded images
    def blob(m):
        bid = m.group(1)
        return prefix + 'assets/img/' + img_names[bid]
    text = re.sub(r'/_blob/([a-f0-9]{32})', blob, text)
    return text


def launch_edits(name, body, logic):
    """Changes for the live site: drop mockup-only notes and unfinished parts."""
    if name == 'Main':
        # adhesive-overlay detail page is not finished yet: point its card to the related Q&A
        # real map instead of the placeholder
        body = body.replace(
            '<span style="font-size: 13px; color: #52575B">[네이버 지도 — 실제 사이트에서 지도 API로 연결]</span>',
            '<iframe title="위드치과보철과 위치 지도" src="https://maps.google.com/maps?q=%EC%84%9C%EC%9A%B8%20%EC%98%81%EB%93%B1%ED%8F%AC%EA%B5%AC%20%EC%97%AC%EC%9D%98%EB%82%98%EB%A3%A8%EB%A1%9C%2053-1&amp;z=17&amp;output=embed" style="width: 100%; height: 100%; border: 0; display: block" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>')
        assert 'iframe' in body
    if name == 'Notice':
        body = re.sub(r'<p style="margin: 48px 0 0; padding: 14px 18px;[^>]*>시안 안내:[\s\S]*?</p>', '', body)
        logic = re.sub(r"\n\{[^\n]*ex: true \},?", '', logic)
        assert 'ex: true' not in logic and '시안 안내' not in body
    if name == 'Privacy':
        body = re.sub(r'<div style="margin-top: 32px; padding: 14px 18px;[^>]*>시안 안내:[\s\S]*?</div>', '', body)
        assert '시안 안내' not in body
    return body, logic


def head_meta(name, cfg, prefix, faq=None):
    url = DOMAIN + '/' + cfg['path']
    out = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>%s</title>' % html.escape(cfg['title']),
        '<meta name="description" content="%s">' % html.escape(cfg['desc']),
        '<link rel="canonical" href="%s">' % url,
        '<link rel="icon" href="%sassets/img/favicon.png" type="image/png">' % prefix,
        '<link rel="apple-touch-icon" href="%sassets/img/apple-touch-icon.png">' % prefix,
        '<meta name="theme-color" content="#E8E6E1">',
        '<meta name="google-site-verification" content="vGXlTegwWYiN8vdYWh1z_Od-bCP5DrzpgO15uxwzsSw">',
        '<meta name="naver-site-verification" content="ce676631b4a5442c82d37e354cb9b1e44ef7202b">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="위드치과보철과 WITH Dental Clinic">',
        '<meta property="og:title" content="%s">' % html.escape(cfg['title']),
        '<meta property="og:description" content="%s">' % html.escape(cfg['desc']),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s/assets/img/og.jpg">' % DOMAIN,
        '<meta property="og:locale" content="%s">' % {'en': 'en_US', 'zh-Hans': 'zh_CN', 'zh-Hant': 'zh_HK'}.get(cfg['lang'], 'ko_KR'),
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if cfg.get('noindex'):
        out.append('<meta name="robots" content="noindex, follow">')
    if name in ('Main', 'English', 'Chinese', 'ChineseTraditional'):
        out += [
            '<link rel="alternate" hreflang="ko" href="%s/">' % DOMAIN,
            '<link rel="alternate" hreflang="en" href="%s/en/">' % DOMAIN,
            '<link rel="alternate" hreflang="zh-Hans" href="%s/zh/">' % DOMAIN,
            '<link rel="alternate" hreflang="zh-Hant" href="%s/zh-hant/">' % DOMAIN,
            '<link rel="alternate" hreflang="x-default" href="%s/">' % DOMAIN,
        ]
        ld = dict(JSONLD_CLINIC)
        if name == 'English':
            ld = dict(ld, name='WITH Dental Clinic Seoul', alternateName=['위드치과보철과', 'WITH Dental Prosthodontics Clinic'],
                      url=DOMAIN + '/en/',
                      description='Family-run dental clinic in Yeouido, Seoul, since 1993. Board-certified prosthodontist and orthodontist; consultations in English. By appointment only.',
                      address=dict(JSONLD_CLINIC['address'], streetAddress='#401, 4F, Daeo Bldg., 53-1 Yeouinaru-ro', addressLocality='Yeongdeungpo-gu', addressRegion='Seoul'))
        if name == 'Chinese':
            ld = dict(ld, name='WITH 牙科（WITH Dental Clinic Seoul）', alternateName=['WITH Dental Clinic Seoul', '위드치과보철과'],
                      url=DOMAIN + '/zh/',
                      description='首尔汝矣岛的牙科诊所，自1993年起在同一地点诊疗。口腔修复科与口腔正畸科专科医生协同诊疗。可提前预约牙科专业中文翻译。100% 预约制。',
                      address=dict(JSONLD_CLINIC['address'], streetAddress='#401, 4F, Daeo Bldg., 53-1 Yeouinaru-ro', addressLocality='Yeongdeungpo-gu', addressRegion='Seoul'))
        if name == 'ChineseTraditional':
            ld = dict(ld, name='WITH 牙科（WITH Dental Clinic Seoul）', alternateName=['WITH Dental Clinic Seoul', '위드치과보철과'],
                      url=DOMAIN + '/zh-hant/',
                      description='首爾汝矣島的牙科診所，自1993年起在同一地點診療。口腔修復科與口腔正畸科專科醫生協同診療。可提前預約牙科專業中文翻譯。100% 預約制。',
                      address=dict(JSONLD_CLINIC['address'], streetAddress='#401, 4F, Daeo Bldg., 53-1 Yeouinaru-ro', addressLocality='Yeongdeungpo-gu', addressRegion='Seoul'))
        out.append('<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False))
    if cfg.get('about'):
        out.append('<script type="application/ld+json">%s</script>' % json.dumps({
            "@context": "https://schema.org", "@type": "MedicalWebPage", "url": url, "name": cfg['title'],
            "description": cfg['desc'], "inLanguage": "ko",
            "about": [{"@type": "MedicalProcedure", "name": a} for a in cfg['about']],
            "provider": {"@type": "Dentist", "@id": DOMAIN + "/#clinic", "name": "위드치과보철과",
                         "telephone": JSONLD_CLINIC['telephone'], "address": JSONLD_CLINIC['address']},
            "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "위드치과보철과", "item": DOMAIN + "/"},
                {"@type": "ListItem", "position": 2, "name": cfg['crumb'], "item": url}]}
        }, ensure_ascii=False))
    if faq:
        out.append('<script type="application/ld+json">%s</script>' % json.dumps({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]
        }, ensure_ascii=False))
    return '\n'.join(out)


def page_html(name, cfg, helmet, body, logic, props, prefix, prerendered='', faq=None):
    return '''<!doctype html>
<html lang="%s">
<head>
%s
%s
<link rel="stylesheet" href="%sassets/site.css">
</head>
<body>
<div id="wd-root">%s</div>
<template id="wd-tpl">%s</template>
<script src="%sassets/wd-runtime.js"></script>
<script>
%s
WD.boot(Component, %s);
</script>
</body>
</html>
''' % (cfg['lang'], head_meta(name, cfg, prefix, faq), helmet.strip(), prefix, prerendered, body, prefix, logic.strip(), json.dumps(props))


def main():
    if os.path.exists(OUT):
        keep = os.path.join(OUT, '.git')
        for f in os.listdir(OUT):
            if f == '.git':
                continue
            p = os.path.join(OUT, f)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT + '/assets/img', exist_ok=True)
    shutil.copy(BUILD + '/wd-runtime.js', OUT + '/assets/wd-runtime.js')
    shutil.copy(BUILD + '/site.css', OUT + '/assets/site.css')

    img_names = {}
    used = set()
    for name in PAGES:
        used.update(re.findall(r'/_blob/([a-f0-9]{32})', open('%s/%s.dc.html' % (SRC, name)).read()))
    for bid, path in BLOBMAP.items():
        fn = os.path.basename(path)
        img_names[bid] = fn
        if bid in used:
            shutil.copy(path, OUT + '/assets/img/' + fn)

    # favicon from the WDC mark
    logo = Image.open(os.path.join(ROOT, 'images/web-logo.png')).convert('RGBA')
    mark = logo.crop((0, 0, 640, 222))
    for size, fn in ((64, 'favicon.png'), (180, 'apple-touch-icon.png')):
        sq = Image.new('RGBA', (size, size), (232, 230, 225, 255))
        w = int(size * 0.82)
        h = int(w * mark.height / mark.width)
        m = mark.resize((w, h), Image.LANCZOS)
        sq.alpha_composite(m, ((size - w) // 2, (size - h) // 2))
        sq.save(OUT + '/assets/img/' + fn)
    # share image
    og = Image.open(os.path.join(ROOT, 'images/hero1.jpg')).convert('RGB')
    r = 1200 / 630
    W, H = og.size
    if W / H > r:
        nw = int(H * r); og = og.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:
        nh = int(W / r); og = og.crop((0, (H - nh) // 2, W, (H - nh) // 2 + nh))
    og.resize((1200, 630), Image.LANCZOS).save(OUT + '/assets/img/og.jpg', quality=85)

    pages = {}
    for name, cfg in PAGES.items():
        src = open('%s/%s.dc.html' % (SRC, name)).read()
        helmet, body, logic, props = split_dc(src)
        body, logic = launch_edits(name, body, logic)
        depth = cfg['path'].count('/')
        prefix = '../' * depth
        body = rewrite(body, prefix, img_names)
        helmet = rewrite(helmet, prefix, img_names)
        logic = rewrite(logic, prefix, img_names)
        out_dir = OUT + '/' + cfg['path']
        os.makedirs(out_dir, exist_ok=True)
        pages[name] = (cfg, helmet, body, logic, props, prefix, out_dir)
        open(out_dir + 'index.html', 'w').write(page_html(name, cfg, helmet, body, logic, props, prefix))

    # prerender each page and pull FAQ text for structured data
    res = subprocess.run(['node', BUILD + '/prerender.js', OUT] + [p[6] + 'index.html' for p in pages.values()],
                         capture_output=True, text=True, cwd=BUILD)
    if res.returncode != 0:
        raise SystemExit(res.stderr)
    rendered = json.loads(res.stdout)
    for (name, (cfg, helmet, body, logic, props, prefix, out_dir)) in pages.items():
        r = rendered[out_dir + 'index.html']
        faq = r['faq'] or None
        open(out_dir + 'index.html', 'w').write(page_html(name, cfg, helmet, body, logic, props, prefix, r['html'], faq))

    shutil.copy(BUILD + '/llms.txt', OUT + '/llms.txt')
    open(OUT + '/CNAME', 'w').write('withdental.kr\n')
    open(OUT + '/.nojekyll', 'w').write('')
    open(OUT + '/robots.txt', 'w').write('User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % DOMAIN)
    urls = ''.join('  <url><loc>%s/%s</loc></url>\n' % (DOMAIN, c['path']) for c in PAGES.values() if not c.get('noindex'))
    open(OUT + '/sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)
    open(OUT + '/404.html', 'w').write('''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>페이지를 찾을 수 없습니다 | 위드치과보철과</title><meta name="robots" content="noindex"><style>body{margin:0;font-family:system-ui,sans-serif;background:#E8E6E1;color:#1C1F21;display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center}a{color:#26383A}</style></head><body><main><p style="letter-spacing:.2em;font-size:13px;color:#52575B">404</p><h1 style="font-weight:500">페이지를 찾을 수 없습니다</h1><p><a href="/">위드치과보철과 홈으로</a> · <a href="/en/">English</a></p></main></body></html>''')
    print('built', OUT)


if __name__ == '__main__':
    main()
