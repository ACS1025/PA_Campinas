#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# CSS para o menu hambúrguer
HAMBURGER_CSS = '''    /* Menu Hambúrguer */
.menu-toggle {
    display: none;
    flex-direction: column;
    background: none;
    border: none;
    cursor: pointer;
    padding: 10px 15px;
    gap: 5px;
    z-index: 1001;
}

.menu-toggle span {
    width: 25px;
    height: 3px;
    background-color: #ffffff;
    border-radius: 3px;
    transition: 0.3s ease;
}

.menu-toggle.active span:nth-child(1) {
    transform: rotate(45deg) translate(8px, 8px);
}

.menu-toggle.active span:nth-child(2) {
    opacity: 0;
}

.menu-toggle.active span:nth-child(3) {
    transform: rotate(-45deg) translate(7px, -7px);
}

@media (max-width: 768px) {
    .menu-toggle {
        display: flex;
        position: fixed;
        right: 15px;
        top: 15px;
    }

    nav ul, .navbar {
        flex-direction: column;
        position: fixed;
        top: 60px;
        left: 0;
        right: 0;
        background-color: rgba(20, 20, 20, 0.98);
        gap: 0;
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
        justify-content: flex-start;
        padding: 0 !important;
        border-radius: 0;
        box-shadow: inset 0 2px 15px rgba(0, 0, 0, 0.5);
    }

    nav ul.active, .navbar.active {
        max-height: 500px;
        padding: 15px 0 !important;
    }

    nav ul li, .navbar a {
        width: 100%;
        text-align: center;
    }

    nav ul li a, .navbar a {
        display: block;
        border-radius: 0;
        padding: 15px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    nav ul li:hover, .navbar a:hover {
        background-color: rgba(23, 23, 175, 0.6) !important;
    }

    nav ul li:last-child a, .navbar a:last-child {
        border-bottom: none !important;
    }
}
'''

# JavaScript para o menu hambúrguer
HAMBURGER_JS = '''
    // Menu Hambúrguer - Responsivo
    document.addEventListener('DOMContentLoaded', function() {
        const menuToggle = document.getElementById('menuToggle');
        const navMenu = document.querySelector('nav ul') || document.querySelector('.navbar');

        if (menuToggle && navMenu) {
            menuToggle.addEventListener('click', function() {
                menuToggle.classList.toggle('active');
                navMenu.classList.toggle('active');
            });

            // Fecha o menu ao clicar em um link
            const navLinks = navMenu.querySelectorAll('a');
            navLinks.forEach(link => {
                link.addEventListener('click', function() {
                    menuToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                });
            });

            // Fecha o menu ao clicar fora
            document.addEventListener('click', function(event) {
                const isClickInsideNav = navMenu.contains(event.target);
                const isClickOnToggle = menuToggle.contains(event.target);
                
                if (!isClickInsideNav && !isClickOnToggle && navMenu.classList.contains('active')) {
                    menuToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });
        }
    });
'''

# HTML do botão hambúrguer
HAMBURGER_BUTTON = '''  <button class="menu-toggle" id="menuToggle">
    <span></span>
    <span></span>
    <span></span>
  </button>
'''

def process_file(filepath, has_nav_tag=True):
    """Process a single HTML file to add hamburger menu."""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. Adicionar CSS antes de </style>
        if '</style>' in content:
            # Find the last occurrence of </style> and add CSS before it
            last_style_index = content.rfind('</style>')
            if last_style_index != -1:
                content = content[:last_style_index] + HAMBURGER_CSS + '\n' + content[last_style_index:]
                print(f"✓ CSS adicionado a {filepath}")
            else:
                print(f"✗ </style> não encontrado em {filepath}")
                return False
        
        # 2. Adicionar botão hamburguer antes de <nav> ou .navbar
        if has_nav_tag:
            # Para arquivos com <nav>
            if '<nav>' in content:
                content = content.replace('<nav>', HAMBURGER_BUTTON + '\n  <nav>', 1)
                print(f"✓ Botão hambúrguer adicionado a {filepath}")
            else:
                print(f"✗ <nav> não encontrado em {filepath}")
                return False
        else:
            # Para arquivos com .navbar
            if 'class="navbar"' in content or "class='navbar'" in content:
                # Procura por <div class="navbar"> ou <div class='navbar'>
                if '<div class="navbar">' in content:
                    content = content.replace('<div class="navbar">', HAMBURGER_BUTTON + '\n    <div class="navbar">', 1)
                    print(f"✓ Botão hambúrguer adicionado a {filepath}")
                elif "<div class='navbar'>" in content:
                    content = content.replace("<div class='navbar'>", HAMBURGER_BUTTON + "\n    <div class='navbar'>", 1)
                    print(f"✓ Botão hambúrguer adicionado a {filepath}")
                else:
                    print(f"✗ .navbar não encontrado em {filepath}")
                    return False
            else:
                print(f"✗ .navbar não encontrado em {filepath}")
                return False
        
        # 3. Adicionar JavaScript antes de </script>
        if '</script>' in content:
            last_script_index = content.rfind('</script>')
            if last_script_index != -1:
                content = content[:last_script_index] + HAMBURGER_JS + '\n' + content[last_script_index:]
                print(f"✓ JavaScript adicionado a {filepath}")
            else:
                print(f"✗ </script> não encontrado em {filepath}")
                return False
        
        # Salvar o arquivo
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {filepath} atualizado com sucesso!")
            return True
        else:
            print(f"⚠ Nenhuma mudança feita em {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao processar {filepath}: {e}")
        return False

def main():
    base_path = "c:\\Users\\komando.campinas\\Documents\\GitHub\\PA_Campinas"
    
    # Arquivos com <nav>
    nav_files = [
        'brief.html',
        'convite.html',
        'videos.html',
        'TestePiloto.html'
    ]
    
    # Arquivos com .navbar
    navbar_files = [
        'comunicado.html',
        'solicitacao-escolta.html',
        'briefingoff.html'
    ]
    
    print("=" * 60)
    print("Iniciando adição de menu hambúrguer...")
    print("=" * 60)
    
    success_count = 0
    
    # Processar arquivos com <nav>
    print("\n📌 Arquivos com <nav>:")
    for file in nav_files:
        filepath = os.path.join(base_path, file)
        if os.path.exists(filepath):
            if process_file(filepath, has_nav_tag=True):
                success_count += 1
        else:
            print(f"✗ Arquivo não encontrado: {filepath}")
    
    # Processar arquivos com .navbar
    print("\n📌 Arquivos com .navbar:")
    for file in navbar_files:
        filepath = os.path.join(base_path, file)
        if os.path.exists(filepath):
            if process_file(filepath, has_nav_tag=False):
                success_count += 1
        else:
            print(f"✗ Arquivo não encontrado: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"Processamento concluído: {success_count}/{len(nav_files) + len(navbar_files)} arquivos atualizados")
    print("=" * 60)

if __name__ == "__main__":
    main()
