# ALERA

Site e prévia do app de alertas de risco de chuva.

Para abrir, use `front-end/index.html` (site) ou `front-end/app/login.html` (login).

## Estrutura

```
front-end/
├── index.html      landing do site
├── css/
│   ├── tokens.css  cores, fontes e espaçamentos (compartilhado)
│   ├── base.css    estilos globais
│   ├── site.css
│   ├── login.css
│   ├── app.css
│   └── admin.css   linkar depois de app.css
├── js/
│   ├── site.js
│   ├── login.js
│   └── admin.js
├── assets/
│   ├── img/        fotos, logos e imagens
│   └── icons/      ícones SVG
└── app/
    ├── login.html
    ├── app.html
    └── admin.html  administração (prévia, sem servidor)
```

`referencias/` guarda o material de apoio e fica fora do repositório.
