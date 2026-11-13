"""Monta guia/guia-site-3d.html a partir do PROMPT.md. O PDF sai do Chrome sem interface."""
import os, re, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prompt = re.search(r"```text\n(.*?)```", open(os.path.join(ROOT, 'PROMPT.md'), encoding='utf-8').read(), re.S).group(1)
FONTS = '../site/fonts'
DEMO = 'https://apto-3d-demo.maxcarrau.workers.dev'
REPO = 'https://github.com/maximilianocarrau123-debug/site-3d-claude-blender'


def table(head, rows):
    h = ''.join(f'<th>{c}</th>' for c in head)
    b = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


passos = table(['Passo', 'O que acontece', 'O que você entrega', 'O que o Claude devolve'], [
    ['<b>1 · Objeto</b>', 'Escolha de um objeto herói e do objetivo da página.', 'O negócio e o objeto.', 'Confirmação, ou uma alternativa melhor pra 3D.'],
    ['<b>2 · Referência</b>', 'O Claude lê imagens do objeto e sites de que você gosta.', 'Fotos, planta ou desenho. De 1 a 3 sites.', 'Uma tabela do que aproveita de cada um.'],
    ['<b>3 · Marca</b>', 'Cores e fontes viram variáveis de CSS.', 'Seu manual de marca, ou só as cores.', 'O arquivo de tokens e as regras da página.'],
    ['<b>4 · Modelagem</b>', 'O Claude escreve o script, o Blender roda, o Claude olha o render e corrige.', 'Só o "ok" ou o que ajustar.', 'Renders lado a lado com a referência.'],
    ['<b>5 · Exportar</b>', 'O modelo vira um arquivo <code>.glb</code> leve.', 'Nada.', 'O arquivo e o peso dele.'],
    ['<b>6 · Palco</b>', 'Luz, sombra, material e câmera no navegador.', 'Nada.', 'O link local pra você abrir.'],
    ['<b>7 · Coreografia</b>', 'Uma pose de câmera por seção. O scroll mistura as poses.', 'Quais partes do objeto merecem uma parada.', 'A câmera viajando conforme você rola.'],
    ['<b>8 · Página</b>', 'Título, textos, números e botões por cima do 3D.', 'Os dados reais do produto.', 'A página completa.'],
    ['<b>9 · Polimento</b>', 'Celular, performance e publicação.', 'O "pode publicar".', 'O link no ar.'],
])

ideias = table(['Negócio', 'Objeto herói', 'O scroll mostra', 'Módulo extra'], [
    ['Imobiliária, construtora', 'Planta do apartamento', 'Cômodo por cômodo', 'Prédio + voo de drone · sol'],
    ['Loja de produto', 'O produto (tênis, relógio, garrafa)', 'Cada diferencial: sola, tecido, fecho', 'Troca de cor'],
    ['Móveis, marcenaria', 'O móvel', 'Encaixes, gavetas, acabamento', 'Troca de madeira'],
    ['Indústria, máquinas', 'A máquina', 'Cada etapa do processo', 'Vista explodida'],
    ['Arquitetura, engenharia', 'A casa ou o galpão', 'Fachada, estrutura, cobertura', 'Sol nas quatro estações'],
    ['Eventos', 'O estande ou o palco', 'Entrada, área de atendimento, telão', 'Voo de fora pra dentro'],
    ['Clínica, odontologia', 'O equipamento ou a sala', 'Cada etapa do atendimento', '—'],
    ['Embalagem, alimentos', 'A embalagem', 'Rótulo, tampa, o que tem dentro', 'Troca de sabor'],
])

licoes = [
    ('Volta fechada é o segredo.', 'O Claude não acerta o 3D de primeira. Ele acerta porque renderiza, olha a imagem e corrige. Na live foram 3 voltas no apartamento. Exija isso no prompt.'),
    ('Referência com medida vira régua.', 'A planta tinha as cotas escritas. O Claude descobriu que 1 pixel valia 1 centímetro e modelou tudo em escala real. Sem medida, mande uma foto com algo de tamanho conhecido.'),
    ('Textura feita no Blender não chega no site.', 'Só imagem ligada na cor base é exportada no <code>.glb</code>. Por isso as texturas foram geradas em Python e salvas como JPEG.'),
    ('Textura ligada apaga a cor.', 'Na segunda volta todos os tecidos saíram brancos: a textura cinza substituía a cor do material. Em peça colorida, use cor pura.'),
    ('O primeiro print sempre estoura.', 'Parede branca demais e nenhuma sombra. Baixe a exposição e deixe o sol bem mais forte que a luz ambiente.'),
    ('Câmera por pose, não por posição.', 'Alvo, ângulo e distância. Assim cada seção é uma linha de código e ajustar um enquadramento leva segundos.'),
    ('Distância se mistura em escala logarítmica.', 'Pra voar de 260 m até 15 m sem dar um tranco no final, interpole o logaritmo da distância.'),
    ('No celular o objeto sobe.', 'Em tela em pé o cartão de texto cobre o 3D. Desloque a imagem pra metade de cima e compacte o cartão.'),
    ('Parede cortada mostra mais.', 'Em maquete aberta, parede inteira esconde o cômodo quando a câmera desce. Corte a 1,5 m.'),
    ('Declare o que é chute.', 'O andar, a posição da unidade e a orientação solar foram inventados. A página avisa. Peça ao Claude pra sempre separar o medido do estimado.'),
]
licoes_html = ''.join(f'<li><b>{a}</b> {b}</li>' for a, b in licoes)

page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Guia · Site 3D com Claude + Blender</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
@font-face{{font-family:Dotemp;src:url({FONTS}/DotempRegular.ttf)}}
@font-face{{font-family:DotempPx;src:url({FONTS}/Dotemp8bit.ttf)}}
@page{{size:A4;margin:0}}
*{{box-sizing:border-box;margin:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{background:#050507;color:#F2F3FF;font:12.5px/1.6 Geist,system-ui,sans-serif}}
.pg{{width:210mm;min-height:297mm;padding:17mm 16mm 15mm;page-break-after:always;position:relative;background:#050507;overflow:hidden}}
.pg::before{{content:"";position:absolute;right:-40mm;top:-40mm;width:150mm;height:150mm;background:radial-gradient(closest-side,rgba(36,48,204,.38),transparent);pointer-events:none}}
.pg>*{{position:relative}}
.k{{font:500 8.5px 'Geist Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:#9AA0C8}}
h1,h2{{font-family:Dotemp;font-style:italic;font-weight:400}}
h1{{font-size:58px;line-height:1;margin:14px 0 16px}}
h2{{font-size:34px;line-height:1.05;margin:8px 0 12px}}
h1 i,h2 i{{font-family:DotempPx;font-style:normal;color:#CCD8FC}}
h3{{font:600 13.5px Geist;margin:16px 0 6px;color:#F2F3FF}}
p{{color:#B4B9DA;margin:0 0 9px}}.lead{{font-size:14.5px;color:#C9CEEA;max-width:150mm}}
b{{color:#F2F3FF;font-weight:600}}a{{color:#8AA2FF;text-decoration:none}}
code{{font:400 10.5px 'Geist Mono',monospace;color:#CCD8FC;background:#10143A;padding:1px 5px;border-radius:4px}}
pre{{font:400 8.6px/1.5 'Geist Mono',monospace;color:#DFE6FF;background:#0B0E28;border:1px solid #1D1F2E;border-radius:10px;padding:11px 13px;white-space:pre-wrap;margin:8px 0}}
pre.big{{font-size:10.3px;line-height:1.62;padding:16px 18px}}
table{{width:100%;border-collapse:collapse;margin:10px 0;font-size:11px}}
th{{text-align:left;font:500 8px 'Geist Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#6B6F8E;padding:6px 8px 6px 0;border-bottom:1px solid #2A2E4A}}
td{{padding:7px 8px 7px 0;border-bottom:1px solid #1D1F2E;color:#B4B9DA;vertical-align:top}}
ol,ul{{padding-left:18px;color:#B4B9DA}}li{{margin:0 0 7px}}
img{{width:100%;border-radius:10px;display:block;border:1px solid #1D1F2E}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}}.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:10px 0}}
.cap{{font:500 8px 'Geist Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#6B6F8E;margin-top:5px}}
.box{{border:1px solid #2A2E4A;border-radius:12px;padding:12px 14px;margin:10px 0;background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.02))}}
.box p:last-child{{margin:0}}
.ft{{position:absolute;left:16mm;right:16mm;bottom:8mm;display:flex;justify-content:space-between;font:500 8px 'Geist Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#4D5173}}
.wm{{font:400 20px Dotemp;font-style:italic;color:#F2F3FF}}.wm b{{font-family:DotempPx;font-weight:400;font-style:normal;color:#CCD8FC}}
</style></head><body>

<section class="pg">
  <div class="wm">c<b>o</b>re</div>
  <div style="height:22mm"></div>
  <div class="k">Guia · Claude Code + Blender</div>
  <h1>Site 3D pra qualquer <i>negócio.</i></h1>
  <p class="lead">O método em 9 passos, o prompt pronto e as lições da live em que um apartamento saiu de uma planta em 2D e virou um site com voo de drone e simulador de sol. Sem baixar modelo 3D e sem gerador de 3D.</p>
  <div style="height:8mm"></div>
  <img src="img/hero.jpg">
  <div class="cap">O resultado da live · {DEMO.replace('https://','')}</div>
  <div class="box" style="margin-top:9mm"><p><b>Como usar este PDF:</b> abra o Claude Code numa pasta vazia, anexe este arquivo e escreva: <i>"Leia este guia e comece pelo passo 1. Meu negócio é ___ e o objeto 3D é ___."</i> O Claude conduz o resto.</p></div>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>01</span></div>
</section>

<section class="pg">
  <div class="k">01 / O que você vai construir</div>
  <h2>Um objeto, uma câmera, um <i>scroll.</i></h2>
  <p class="lead">A pessoa rola a página e a câmera viaja em volta de um objeto 3D, parando em cada parte que importa. O texto entra ao lado. É isso. O resto é variação.</p>
  <div class="g2">
    <div><img src="img/voo.jpg"><div class="cap">A câmera entra e o prédio fica transparente</div></div>
    <div><img src="img/sala.jpg"><div class="cap">Uma parada por cômodo, com as medidas</div></div>
    <div><img src="img/sol.jpg"><div class="cap">Sol real por hora, estação e face da varanda</div></div>
    <div><img src="img/planta.jpg"><div class="cap">O final volta pro desenho 2D</div></div>
  </div>
  <h3>Links</h3>
  <p>Ver funcionando: <a href="{DEMO}">{DEMO}</a><br>Código completo: <a href="{REPO}">{REPO}</a></p>
  <h3>O que precisa estar instalado</h3>
  <ul>
    <li><b>Claude Code</b>, com um modelo atual.</li>
    <li><b>Blender</b> 4 ou mais novo. No Mac: <code>brew install --cask blender</code>. No Windows: instalador do site blender.org.</li>
    <li><b>Python 3</b> com duas bibliotecas: <code>pip3 install pillow numpy</code>.</li>
  </ul>
  <p>Você não abre o Blender nenhuma vez. O Claude roda ele por linha de comando.</p>
  <div class="box"><p><b>Por que Blender e não só código de navegador?</b> No navegador as formas são básicas: caixa, esfera, cilindro. No Blender o Claude tem chanfro, curva, suavização e material de verdade. E o resultado sai num arquivo só, que qualquer site carrega.</p></div>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>02</span></div>
</section>

<section class="pg">
  <div class="k">02 / O método</div>
  <h2>Os 9 <i>passos.</i></h2>
  <p class="lead">Cada passo tem uma entrega sua e uma devolução do Claude. Ele só avança quando você diz "ok".</p>
  {passos}
  <h3>Módulos opcionais</h3>
  <ul>
    <li><b>Contexto.</b> Modelar também o que está em volta do objeto e fazer a câmera voar de fora pra dentro. Na live: o prédio de 28 andares e a cidade.</li>
    <li><b>Sol.</b> Luz natural calculada pela latitude da cidade, pela estação e pela hora. Mostra sombra, nascer, pôr e horas de sol direto.</li>
    <li><b>Variações.</b> Botões que trocam cor, material ou acabamento.</li>
  </ul>
  <div class="g3">
    <div><img src="img/blender-v1.jpg"><div class="cap">Volta 1 · almofada virou ovo</div></div>
    <div><img src="img/blender-apto.jpg"><div class="cap">Volta 3 · corrigido</div></div>
    <div><img src="img/blender-predio.jpg"><div class="cap">O prédio, a partir de 2 fotos</div></div>
  </div>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>03</span></div>
</section>

<section class="pg">
  <div class="k">03 / O prompt</div>
  <h2>O prompt <i>mestre.</i></h2>
  <p>Cole numa pasta vazia do Claude Code. Troque só o que está entre chaves. Se não souber alguma resposta, apague a linha: o Claude pergunta no passo certo.</p>
  <pre class="big">{html.escape(prompt[:prompt.index('OS 9 PASSOS')].rstrip())}</pre>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>04</span></div>
</section>

<section class="pg">
  <div class="k">03 / O prompt · continuação</div>
  <pre class="big">{html.escape(prompt[prompt.index('OS 9 PASSOS'):].rstrip())}</pre>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>05</span></div>
</section>

<section class="pg">
  <div class="k">04 / Pra qualquer empresa</div>
  <h2>Troque o objeto, o método é o <i>mesmo.</i></h2>
  <p class="lead">A pergunta que decide tudo: qual é a coisa que o seu cliente precisa enxergar pra comprar? Essa coisa é o objeto herói.</p>
  {ideias}
  <h3>Como escolher um bom objeto</h3>
  <ul>
    <li><b>Reconhecível de qualquer ângulo.</b> Ele vai girar. Objeto que só faz sentido de frente não serve.</li>
    <li><b>Feito de partes.</b> Cada parte vira uma parada da câmera e uma seção da página.</li>
    <li><b>Com medida.</b> Largura, peso, capacidade. Cada seção leva dois números reais.</li>
    <li><b>Formas duras são mais fáceis.</b> Móvel, máquina, prédio e embalagem saem bem. Rosto, bicho e tecido solto são difíceis.</li>
  </ul>
  <h3>O que mandar de referência</h3>
  <ul>
    <li><b>Do objeto:</b> fotos de vários lados, desenho técnico ou planta. Quanto mais cotas, melhor.</li>
    <li><b>Do site:</b> um a três sites de que você gosta, por print ou por link.</li>
    <li><b>Da marca:</b> cores e fontes. Se não tiver, peça uma paleta simples no passo 3.</li>
  </ul>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>06</span></div>
</section>

<section class="pg">
  <div class="k">05 / O que a live ensinou</div>
  <h2>Dez lições pra não <i>travar.</i></h2>
  <ol>{licoes_html}</ol>
  <h3>Se algo der errado</h3>
  {table(['Sintoma', 'O que pedir ao Claude'], [
      ['Objeto todo branco ou estourado', '"Baixe a exposição e aumente o contraste entre sol e luz ambiente."'],
      ['Objeto passa atrás do texto', '"Afaste a câmera nessa pose e desloque o objeto pro lado oposto do cartão."'],
      ['Cores sumiram depois de exportar', '"Confira se alguma textura está substituindo a cor base do material."'],
      ['Site pesado no celular', '"Reduza a resolução, o mapa de sombra e a quantidade de objetos no celular."'],
      ['O modelo não parece a referência', '"Coloque o render e a referência lado a lado e liste as cinco maiores diferenças."'],
  ])}
  <div class="box"><p><b>O repositório é seu ponto de partida.</b> Se preferir não começar do zero, clone <a href="{REPO}">o código da live</a> e peça ao Claude: <i>"Adapte este site pro meu negócio ___, trocando o objeto por ___."</i></p></div>
  <p style="margin-top:8mm">Quer ver os próximos? Me segue no Instagram: <b>@maxcarrau.ia</b></p>
  <div class="ft"><span>Site 3D com Claude + Blender</span><span>07</span></div>
</section>
</body></html>'''
out = os.path.join(ROOT, 'guia', 'guia-site-3d.html')
open(out, 'w', encoding='utf-8').write(page)
print(out)
