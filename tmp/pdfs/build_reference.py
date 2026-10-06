from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'opcodes_C64.pdf'
for name, fn in [('Body','arial.ttf'),('Bold','arialbd.ttf'),('Mono','consola.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/'+fn))
W,H = A4
LEFT=36
WIDTH=W-72
NAVY=colors.HexColor('#162C46')
TEAL=colors.HexColor('#007F82')
MUTED=colors.HexColor('#526276')
LIGHT=colors.HexColor('#EDF5F6')
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=9.5,leading=13,textColor=NAVY),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=9,leading=11.8,textColor=NAVY),
 'small':ParagraphStyle('small',fontName='Body',fontSize=8,leading=10.6,textColor=MUTED),
 'head':ParagraphStyle('head',fontName='Bold',fontSize=9,leading=12,textColor=colors.white),
 'mono':ParagraphStyle('mono',fontName='Mono',fontSize=9,leading=11.8,textColor=TEAL),
}
pages=[]
def add(title,subtitle,headers,rows,widths,notes=()):
    pages.append(dict(title=title,subtitle=subtitle,headers=headers,rows=rows,widths=widths,notes=notes))
def rows(s):
    return [line.split('|') for line in s.strip().splitlines()]

pages.append(dict(title='C64 / Guía rápida',subtitle='6510 + Kick Assembler 5.25',cover=True))
add('01 / Registros y direccionamiento','Qué significa cada operando. Los modos disponibles dependen de la instrucción.',
 ['Registro / flag','Función'],rows('''
A / X / Y|Registros de 8 bits. A: acumulador; X e Y: índices y datos. Sus valores van de 0 a 255.
PC / SP|PC: dirección de la próxima instrucción, 16 bits. SP: índice de la pila en $0100-$01FF, 8 bits.
P|Registro de estado: N V - B D I Z C. B describe el origen de la copia apilada; no es un flag persistente normal.
N / Z|N copia el bit 7 del resultado. Z=1 cuando el resultado es cero; Z=0 en caso contrario.
C / V|C: acarreo; en resta, 1 significa sin préstamo. V: desbordamiento con signo, distinto de C.
D / I|D=1: aritmética decimal BCD en adc/sbc. I=1: bloquea IRQ enmascarables, no NMI.
'''),[105,WIDTH-105],notes=[
 ('MODOS DE DIRECCIONAMIENTO',[
 ['imp / acc','Sin operando. Operación implícita; asl, lsr, rol y ror sin operando actúan sobre A.'],
 ['imm: #valor','Valor literal de 8 bits. No lee esa dirección de memoria.'],
 ['zp: $nn','Dirección de página cero: $0000-$00FF. Instrucción normalmente de 2 bytes.'],
 ['zp,X / zp,Y','Base de página cero más X o Y; la suma vuelve a $00 al superar $FF.'],
 ['abs: $nnnn','Dirección de 16 bits. Instrucción normalmente de 3 bytes.'],
 ['abs,X / abs,Y','Dirección de 16 bits más X o Y. Puede cruzar páginas de 256 bytes.'],
 ['(zp,X)','Primero suma X a zp; luego lee allí un puntero de 16 bits en página cero.'],
 ['(zp),Y','Primero lee el puntero de 16 bits en zp; después suma Y a la dirección obtenida.'],
 ['ind: (addr)','jmp indirecto: toma de memoria la dirección de destino.'],
 ['rel: etiqueta','Saltos condicionales: desplazamiento -128 a +127 desde la instrucción siguiente.'],
 ]),
 'Los punteros guardan primero el byte bajo y después el alto (little endian). En el 6510, jmp indirecto con puntero terminado en $FF toma el byte alto del inicio de esa misma página: evitá ese límite.',
 'Un mnemónico es el nombre, por ejemplo lda. Un opcode es el byte que identifica la instrucción y su modo; lda inmediato usa $A9 y lda absoluto usa $AD.'
])

instructions=rows('''
adc|Suma A + operando + C y deja el byte resultante en A. D selecciona binario o BCD.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z C V
and|AND bit a bit entre A y el operando; deja el resultado en A. Sirve para conservar o borrar bits.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z
asl|Desplaza un bit a la izquierda; entra 0 por bit 0 y el antiguo bit 7 pasa a C.|acc, zp, zpX, abs, absX|N Z C
bcc|Salta si C=0. Tras una comparación sin signo: menor.|rel|-
bcs|Salta si C=1. Tras una comparación sin signo: mayor o igual.|rel|-
beq|Salta si Z=1. No compara: consulta el flag que dejó una instrucción anterior.|rel|-
bit|Z depende de A AND memoria; N y V copian los bits 7 y 6 de memoria. No cambia A.|zp, abs|N Z V
bmi|Salta si N=1: bit 7 del resultado activado.|rel|-
bne|Salta si Z=0: resultado anterior distinto de cero.|rel|-
bpl|Salta si N=0. Incluye el resultado cero.|rel|-
brk|Interrupción por software. Apila PC+2 y estado; usa el vector IRQ/BRK. No equivale a terminar un programa.|imp|I
bvc|Salta si V=0: no hay desbordamiento con signo indicado.|rel|-
bvs|Salta si V=1: hay desbordamiento con signo indicado.|rel|-
clc|Pone C=0. Se usa antes de una suma sin acarreo de entrada.|imp|C
cld|Pone D=0: adc y sbc trabajan en binario.|imp|D
cli|Pone I=0: permite IRQ enmascarables.|imp|I
clv|Pone V=0.|imp|V
cmp|Compara A con el operando mediante una resta sin guardar el resultado. A se conserva.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z C
cpx|Compara X con el operando; no modifica X.|imm, zp, abs|N Z C
cpy|Compara Y con el operando; no modifica Y.|imm, zp, abs|N Z C
dec|Resta 1 al byte de memoria. $00 pasa a $FF. No modifica C.|zp, zpX, abs, absX|N Z
dex|Resta 1 a X; 0 pasa a 255.|imp|N Z
dey|Resta 1 a Y; 0 pasa a 255.|imp|N Z
eor|XOR bit a bit entre A y el operando. Los bits con máscara 1 se invierten.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z
inc|Suma 1 al byte de memoria. $FF pasa a $00. No modifica C.|zp, zpX, abs, absX|N Z
inx|Suma 1 a X; 255 pasa a 0 y activa Z.|imp|N Z
iny|Suma 1 a Y; 255 pasa a 0 y activa Z.|imp|N Z
jmp|Transfiere el control al destino, sin guardar retorno.|abs, ind|-
jsr|Llama a una subrutina: apila el retorno y salta. rts permite volver.|abs|-
lda|Carga el operando en A. Con # toma un literal; sin # lee memoria.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z
ldx|Carga el operando en X. El modo indexado de memoria usa Y.|imm, zp, zpY, abs, absY|N Z
ldy|Carga el operando en Y. El modo indexado de memoria usa X.|imm, zp, zpX, abs, absX|N Z
lsr|Desplaza un bit a la derecha; entra 0 por bit 7 y el antiguo bit 0 pasa a C. N queda en 0.|acc, zp, zpX, abs, absX|N Z C
nop|No realiza una operación útil; el opcode oficial $EA ocupa 1 byte y tarda 2 ciclos.|imp|-
ora|OR bit a bit entre A y el operando. Una máscara con bits 1 permite activarlos.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z
pha|Apila A. A se conserva; SP disminuye.|imp|-
php|Apila una copia del estado con B y bit 5 en 1.|imp|-
pla|Desapila un byte en A y actualiza N y Z.|imp|N Z
plp|Restaura los flags desde la pila. B y bit 5 no son flags persistentes restaurables.|imp|N V D I Z C
rol|Rota a la izquierda pasando por C: entra el C anterior por bit 0; sale bit 7 hacia C.|acc, zp, zpX, abs, absX|N Z C
ror|Rota a la derecha pasando por C: entra el C anterior por bit 7; sale bit 0 hacia C.|acc, zp, zpX, abs, absX|N Z C
rti|Retorna de una interrupción: restaura estado y PC desde la pila.|imp|N V D I Z C
rts|Retorna de una subrutina: recupera la dirección apilada y suma 1. No restaura los flags.|imp|-
sbc|Calcula A - operando - (1-C). Para restar sin préstamo previo se prepara C=1.|imm, zp, zpX, abs, absX, absY, izX, izY|N Z C V
sec|Pone C=1.|imp|C
sed|Pone D=1: adc y sbc operan en decimal codificado en binario (BCD).|imp|D
sei|Pone I=1: bloquea IRQ enmascarables; NMI sigue habilitada.|imp|I
sta|Guarda A en memoria. No cambia A ni los flags.|zp, zpX, abs, absX, absY, izX, izY|-
stx|Guarda X en memoria. No cambia X ni los flags.|zp, zpY, abs|-
sty|Guarda Y en memoria. No cambia Y ni los flags.|zp, zpX, abs|-
tax|Copia A en X. A se conserva.|imp|N Z
tay|Copia A en Y. A se conserva.|imp|N Z
tsx|Copia SP en X.|imp|N Z
txa|Copia X en A. X se conserva.|imp|N Z
txs|Copia X en SP. No modifica los flags.|imp|-
tya|Copia Y en A. Y se conserva.|imp|N Z
''')
assert len(instructions)==56
for start,end in [(0,19),(19,38),(38,56)]:
    part=instructions[start:end]
    add('02 / Mnemónicos: '+part[0][0]+' - '+part[-1][0],
        'Los 56 oficiales del 6502/6510. Escribilos en minúsculas en Kick Assembler.',
        ['Nombre','Para qué sirve','Modos','Flags'],part,[50,WIDTH-50-112-60,112,60],
        ['zpX = zp,X; zpY = zp,Y; absX = abs,X; absY = abs,Y; izX = (zp,X); izY = (zp),Y. Un guion indica que no modifica flags.',
         'Las descripciones de N/Z/V en aritmética suponen D=0. En el 6510 NMOS, los flags de adc/sbc en modo decimal tienen particularidades: no los interpretes como si describieran siempre el resultado BCD corregido.'])

add('03 / Opcodes no oficiales','Reconocidos por Kick Assembler con .cpu _6502. Referencia avanzada; no necesarios para aprender.',
 ['Nombre / alias','Efecto resumido'],rows('''
ahx / sha|Guarda una combinación de A, X y el byte alto de la dirección +1. Inestable en ciertos casos de direccionamiento.
alr / asr|Combina AND inmediato con desplazamiento lógico a la derecha de A.
anc|AND inmediato; además copia el bit 7 del resultado a C. Opcode $0B.
anc2|Variante de anc con opcode $2B.
arr|Combina AND inmediato y rotación a la derecha de A; C, V y el modo decimal tienen reglas especiales.
axs / sbx|Calcula (A AND X) menos el inmediato y lo deja en X; actualiza N, Z y C.
dcp / dcm|Decrementa memoria y luego la compara con A.
isc / ins / isb|Incrementa memoria y luego la resta de A mediante sbc.
las / lae / lds|Combina memoria AND SP y copia el resultado en A, X y SP.
lax / lxa|Carga A y X a la vez. La forma inmediata $AB tiene comportamiento dependiente del chip.
nop (variantes)|Versiones que consumen operandos, bytes y ciclos adicionales; algunas leen memoria.
rla|Rota memoria a la izquierda y hace AND con A.
rra|Rota memoria a la derecha y suma el resultado a A con acarreo.
sax|Guarda A AND X en memoria, sin cambiar A ni X.
sbc2|Variante inmediata de sbc con opcode $EB.
shx|Almacenamiento enmascarado con X y el byte alto de dirección; comportamiento especial al cruzar página.
shy|Almacenamiento enmascarado con Y y el byte alto de dirección; comportamiento especial al cruzar página.
slo|Desplaza memoria a la izquierda y hace OR con A.
sre|Desplaza memoria a la derecha y hace XOR con A.
tas / shs|Copia A AND X a SP y realiza un almacenamiento enmascarado dependiente de la dirección.
xaa / ane|Operación combinada sobre A, X e inmediato; resultado inestable y dependiente del chip.
'''),[115,WIDTH-115],notes=[
 'El 6510 también tiene bytes KIL/JAM que bloquean la CPU hasta un reset. No aparecen como mnemónico en la tabla de Kick Assembler 5.25.',
 'No confundir con instrucciones del 65C02 o C64 DTV: bra, stz, phx, phy, plx, ply, trb, tsb y las extensiones de esas CPU no pertenecen a la C64 clásica.',
 'Para limitarse al conjunto oficial se puede seleccionar .cpu _6502NoIllegals. El conjunto predeterminado de Kick Assembler es _6502, que admite también los no oficiales.'
])

add('04 / Operadores de Kick Assembler','Se evalúan en Windows durante el ensamblado. No ejecutan cálculos en el 6510.',
 ['Operador','Significado / uso'],[
 ['-x','Negación aritmética: cambia el signo.'],
 ['+ (suma), - (resta)','Suma y resta. + también concatena cadenas.'],
 ['* y /','Multiplicación y división. Los números del lenguaje de script pueden ser fraccionarios.'],
 ['<valor / >valor','Operadores unarios: byte bajo y byte alto. Para $1234 producen $34 y $12.'],
 ['a << n / a >> n','Desplaza bits a izquierda o derecha durante el ensamblado.'],
 ['a & b','AND bit a bit. Útil para máscaras.'],
 ['a | b','OR bit a bit. Combina bits.'],
 ['a ^ b','XOR bit a bit. Invierte las posiciones seleccionadas.'],
 ['~a','Complemento bit a bit. Para restringir a un byte, aplicar máscara $FF.'],
 ['a == b / a != b','Igualdad y desigualdad; producen un booleano.'],
 ['a < b / a > b','Comparaciones menor y mayor. Con dos operandos no extraen bytes.'],
 ['a <= b / a >= b','Comparaciones menor o igual y mayor o igual.'],
 ['!a','Negación lógica de un booleano.'],
 ['a && b / a || b','AND / OR lógicos con evaluación de cortocircuito.'],
 ['cond ? a : b','Expresión condicional: elige a si cond es true; b si es false.'],
 ['=','Asignación en el lenguaje de script. No compara ni almacena en RAM de la C64.'],
 ['+= / -= / *= / /=','Actualiza una variable de ensamblado combinando operación y asignación.'],
 ['x++ / x--','Incremento / decremento posfijo; la expresión devuelve el valor anterior.'],
 ['(...) / [...]','Agrupan expresiones. En operandos de CPU, (...) puede significar direccionamiento indirecto; [...] evita esa ambigüedad.'],
 ['*','Contador de posición actual cuando aparece como valor. Entre dos operandos significa multiplicación.'],
 ],[128,WIDTH-128],notes=[
 'No trasladar toda la sintaxis de PHP/Java/C sin verificar: esta tabla recoge los operadores documentados en el manual instalado. Para resto de división, el manual ofrece la función mod(a,b); % se usa como prefijo binario.',
 'Una expresión como dirección+40 la resuelve el ensamblador. Una instrucción como adc realiza una suma mientras corre el programa: son momentos distintos.'
])

add('05 / Sintaxis, números y texto','Convenciones que vas a consultar al escribir un archivo .asm.',
 ['Forma','Qué significa'],rows('''
42 / $2A / %101010|El mismo número en decimal, hexadecimal y binario. Sin prefijo se interpreta decimal.
#valor|Operando inmediato de una instrucción: el número en sí, no el contenido de una dirección.
nombre:|Define una etiqueta en la posición actual. Referenciarla sin los dos puntos.
!nombre: / !:|Etiqueta reutilizable o anónima. !nombre+ busca la siguiente; !nombre- la anterior; !+ y !- para anónimas.
!++ / !--|Salta dos apariciones de una etiqueta anónima hacia delante / atrás; se pueden repetir los signos.
argumento:|Una etiqueta delante de un operando marca su ubicación dentro de la instrucción. Uso avanzado: código automodificable.
// comentario|Comentario hasta el fin de línea.
/* comentario */|Comentario de bloque, que puede ocupar varias líneas.
;|Separa instrucciones o partes de .for. NO inicia comentarios en Kick Assembler.
{ ... }|Agrupa directivas y crea ámbitos locales según el contexto.
espacio.nombre|Acceso a un símbolo de un namespace o ámbito etiquetado.
@nombre|Busca el símbolo en el ámbito raíz, escapando al ámbito local.
"texto" / 'A'|Cadena y carácter. Su conversión a bytes depende de .encoding.
@"texto"|Cadena con interpretación de secuencias de escape de Kick Assembler.
.abs / .a|Sufijo del mnemónico para forzar direccionamiento absoluto cuando existe.
.zp / .z|Sufijo del mnemónico para forzar página cero cuando existe.
virtual|Opción de un bloque de memoria que define posiciones sin incluir sus bytes en el archivo generado.
true / false / null|Valores booleanos y ausencia de valor en el lenguaje de script.
'''),[120,WIDTH-120],notes=[
 ('CODIFICACIONES PARA .encoding',[
 ['ascii','Codificación ASCII; no es directamente la de la pantalla C64.'],
 ['petscii_upper / petscii_mixed','PETSCII para mayúsculas/gráficos o mayúsculas/minúsculas; adecuado para salida mediante KERNAL.'],
 ['screencode_upper / screencode_mixed','Códigos para la RAM de pantalla en los dos juegos de caracteres. Predeterminado del ensamblador: screencode_mixed.'],
 ]),
 '.encoding transforma texto en bytes al ensamblar; no cambia la fuente ni el modo del VIC-II. Escribir .text tampoco imprime: solamente genera datos.'
])

directives=rows('''
* = dirección|Fija la posición donde se ensamblan los bytes siguientes. No ejecuta ni salta a esa dirección.
.align|Avanza hasta la siguiente frontera de alineación indicada; si ya está alineado, no avanza.
.assert|Comprueba igualdad de expresiones o de bloques ensamblados durante la construcción.
.asserterror|Comprueba que una expresión o bloque produzca un error esperado.
.break|Añade un punto de interrupción a los datos de depuración. No inserta una instrucción brk.
.by|Alias de .byte.
.byte|Emite valores de un byte en el archivo de salida.
.const|Declara un símbolo constante del lenguaje de ensamblado; no reserva RAM.
.cpu|Selecciona conjunto de instrucciones: _6502NoIllegals, _6502, dtv o _65c02.
.define|Ejecuta un bloque en modo de funciones para definir valores; evita registrar salida de ensamblado innecesaria.
.disk|Construye una imagen de disco D64 según sus parámetros y archivos.
.dw|Alias de .dword. Atención: NO es alias de .word.
.dword|Emite valores de 4 bytes en orden little endian.
.encoding|Selecciona la conversión de caracteres a bytes; ver la página de sintaxis.
.enum|Declara una secuencia de constantes, con valores automáticos o explícitos.
.error|Genera un error de ensamblado con un mensaje propio.
.errorif|Genera un error si se cumple una condición; útil para verificar límites y direcciones.
.eval|Evalúa una expresión de script, por ejemplo una asignación o llamada a un método.
.file|Genera un archivo PRG o binario a partir de los segmentos indicados.
.filemodify|Aplica un modificador a la salida del archivo fuente actual.
.filenamespace|Establece un namespace para el resto del archivo fuente.
.fill|Genera bytes repitiendo una expresión; i es el índice de repetición. También admite patrones de valores.
.fillword|Como .fill, pero emite palabras de 2 bytes.
.for|Repite directivas al ensamblar. Puede generar tablas o código repetido; no crea un bucle de CPU por sí solo.
.function|Define una función del lenguaje de script que calcula un resultado al ensamblar.
.if|Incluye o evalúa directivas según una condición de ensamblado. La alternativa se escribe else, sin punto.
.import binary|Incorpora bytes de un archivo binario.
.import c64|Incorpora un archivo omitiendo sus dos primeros bytes de dirección de carga.
.import source|Importa código fuente; forma antigua. Se recomienda #import.
.import text|Importa texto y lo convierte con la codificación activa.
.importonce|Evita importar de nuevo un archivo; forma antigua. Se recomienda #importonce.
.label|Define una etiqueta mediante una expresión; admite referencias hacia delante según el contexto.
.lohifill|Genera dos tablas consecutivas: bytes bajos y altos. La etiqueta asociada ofrece los miembros .lo y .hi.
.macro|Define un bloque expandible con parámetros. Se expande al ensamblar, sin llamada jsr en ejecución.
.memblock|Empieza un bloque de memoria nuevo en la posición actual; permite nombrarlo.
.modify|Aplica un modificador a los bytes generados dentro de un bloque.
.namespace|Crea un espacio de nombres para organizar símbolos y evitar colisiones.
.pc|Forma antigua equivalente a * = dirección.
.plugin|Carga una clase de extensión Java desde su nombre de paquete.
.print|Muestra un mensaje en la consola del ensamblador durante la pasada final.
.printnow|Muestra un mensaje inmediatamente durante la evaluación; puede aparecer en varias pasadas.
.pseudocommand|Define una instrucción de ensamblador personalizada que expande a otras instrucciones o directivas.
.pseudopc|Ensambla direcciones como si el código estuviera en otro lugar; no lo copia ni lo reubica durante la ejecución.
.return|Devuelve un resultado desde una función de script. No es la instrucción rts.
.segment|Selecciona uno o más segmentos de salida según la configuración; admite parámetros del bloque.
.segmentdef|Define un segmento con inicio, límites y otras propiedades.
.segmentout|Emite los bytes de segmentos intermedios dentro del bloque actual.
.struct|Declara una estructura de valores del lenguaje de script; no es por sí sola una estructura en RAM.
.te|Alias de .text.
.text|Emite los bytes de una cadena usando la codificación actual.
.var|Declara una variable de ensamblado. No crea una variable que cambie durante el juego.
.watch|Añade una vigilancia de dirección o rango a los datos de depuración para el debugger compatible.
.while|Repite directivas mientras una expresión de ensamblado sea verdadera.
.wo|Alias de .word.
.word|Emite palabras de 16 bits: byte bajo primero, luego byte alto.
.zp|Marca las etiquetas de un bloque como pertenecientes a página cero, incluso antes de resolverlas.
''')
assert len(directives)==56
for start,end in [(0,19),(19,38),(38,56)]:
    part=directives[start:end]
    add('06 / Directivas: '+part[0][0]+' - '+part[-1][0],
        'Catálogo del manual instalado, incluidos alias, variantes de importación y .watch.',
        ['Directiva','Para qué sirve'],part,[110,WIDTH-110],notes=[
        'Estas directivas se procesan al ensamblar. Las que emiten bytes preparan el archivo; no escriben por sí solas sobre una C64 que ya está ejecutando el programa.',
        'La sintaxis completa de parámetros para segmentos, archivos y discos está en los capítulos 10 y 11 del manual de Kick Assembler.'
        ])

add('07 / Preprocesador y utilidades','El preprocesador selecciona el código fuente antes de su evaluación.',
 ['Directiva','Para qué sirve'],rows('''
#define|Define un símbolo booleano de preprocesador. No es una constante numérica como .const.
#undef|Elimina la definición de un símbolo de preprocesador.
#if|Incluye un bloque si la expresión de símbolos es verdadera.
#elif|Prueba otra condición después de un #if o #elif que no se cumplió.
#else|Incluye la alternativa si ninguna condición anterior se cumplió.
#endif|Termina el bloque condicional.
#import|Incorpora otro archivo fuente.
#importif|Incorpora un archivo fuente solo si se cumple la condición indicada.
#importonce|Dentro de un archivo, evita que se procese más de una vez por importación.
'''),[100,WIDTH-100],notes=[
 'Operadores del preprocesador: !, &&, ||, ==, != y paréntesis. Sus símbolos indican definido/no definido; no son las variables numéricas del programa.',
 ('UTILIDADES DEL ENSAMBLADOR: SELECCIÓN PARA CONSULTA',[
 ['BasicUpstart / BasicUpstart2','Macros incorporadas que generan una línea BASIC para arrancar código máquina. La segunda organiza también las posiciones de memoria.'],
 ['LoadBinary / LoadSid / LoadPicture','Cargan datos, música SID o imágenes para procesarlos al ensamblar. Son funciones, no instrucciones de CPU.'],
 ['List / Hashtable / .struct','Colecciones y estructuras para generar datos mediante el lenguaje de script.'],
 ['floor / ceil / round / mod','Redondeo hacia abajo, arriba, al más cercano y resto de división.'],
 ['sin / cos / toRadians','Cálculos para tablas; las funciones trigonométricas usan radianes.'],
 ['getFilename / getPath','Obtienen el nombre o la ruta del archivo fuente.'],
 ['createFile','Crea una salida adicional mediante el lenguaje de script.'],
 ['cmdLineVars','Tabla de argumentos de script recibidos desde la línea de comandos.'],
 ]),
 'Esta selección de funciones no pretende enumerar todos los métodos de la biblioteca de script. Las directivas y los operadores documentados sí están catalogados en las páginas anteriores.'
])

kernal=rows('''
ACPTR|$FFA5|Recibe un byte del bus serie IEC y lo devuelve en A. Requiere preparar al dispositivo para transmitir.
CHKIN|$FFC6|Selecciona como entrada el archivo lógico cuyo número está en X; debe haberse abierto antes.
CHKOUT|$FFC9|Selecciona como salida el archivo lógico indicado en X; debe haberse abierto antes.
CHRIN|$FFCF|Lee un carácter del canal de entrada en A. Desde teclado usa entrada de línea y puede esperar.
CHROUT|$FFD2|Envía el byte PETSCII de A al canal de salida. En pantalla interpreta caracteres y controles.
CINT|$FF81|Inicializa el editor de pantalla y el VIC-II. Afecta configuración de video y estado del editor.
CIOUT|$FFA8|Envía el byte de A al bus serie; requiere LISTEN/SECOND. La salida puede quedar temporalmente almacenada.
CLALL|$FFE7|Limpia la tabla de archivos lógicos y restaura los canales predeterminados. Para cerrar correctamente archivos de disco, usar CLOSE.
CLOSE|$FFC3|Cierra el archivo lógico indicado en A y libera sus recursos asociados.
CLRCHN|$FFCC|Restaura teclado como entrada y pantalla como salida. No equivale a cerrar todos los archivos.
GETIN|$FFE4|Obtiene un byte del canal de entrada. Con teclado devuelve A=0 si no hay carácter disponible; no espera.
IOBASE|$FFF3|Devuelve la base de E/S en X (bajo) e Y (alto). En C64: $DC00.
IOINIT|$FF84|Inicializa hardware de E/S, como las CIA, y estado asociado. Se usa durante el arranque.
LISTEN|$FFB1|Ordena escuchar al dispositivo IEC cuyo número está en A.
LOAD|$FFD5|A=0 carga; A=1 verifica. Usa SETNAM/SETLFS; X/Y indican destino si dirección secundaria=0. C=1 señala error.
MEMBOT|$FF9C|C=1 lee el límite inferior de memoria en X/Y; C=0 lo fija desde X/Y. X=bajo, Y=alto.
MEMTOP|$FF99|C=1 lee el límite superior de memoria en X/Y; C=0 lo fija. No reubica automáticamente un programa BASIC existente.
OPEN|$FFC0|Abre un archivo lógico usando SETLFS y, si corresponde, SETNAM. C=1 indica error; A contiene el código.
PLOT|$FFF0|C=0 fija cursor: X=fila, Y=columna. C=1 devuelve la posición en esos registros. Coordenadas desde 0.
RAMTAS|$FF87|Inicializa zonas de RAM y punteros del sistema y determina límites de memoria. Rutina de arranque, no de limpieza gráfica.
RDTIM|$FFDE|Lee el reloj de 24 bits: A=byte bajo, X=medio, Y=alto. Se incrementa nominalmente a 60 ticks por segundo.
READST|$FFB7|Devuelve en A el estado de E/S, incluidos indicadores como fin de archivo. No confundir con el registro P del procesador.
RESTOR|$FF8A|Restaura los vectores KERNAL de RAM a sus destinos predeterminados.
SAVE|$FFD8|Guarda un rango. A apunta al par de página cero con el inicio; X/Y contienen el final exclusivo. Preparar SETNAM/SETLFS.
SCNKEY|$FF9F|Explora el teclado y actualiza su buffer. Normalmente se ejecuta desde la IRQ del sistema.
SCREEN|$FFED|Devuelve dimensiones de pantalla: X=columnas, Y=filas; normalmente 40 y 25.
SECOND|$FF93|Envía la dirección secundaria IEC después de LISTEN; A contiene el byte de comando, normalmente $60 OR secundaria.
SETLFS|$FFBA|Prepara A=número de archivo lógico, X=dispositivo, Y=dirección secundaria.
SETMSG|$FF90|Controla mensajes KERNAL con A: bit 7 para mensajes de control, bit 6 para errores; 0 los suprime.
SETNAM|$FFBD|Prepara nombre de archivo: A=longitud, X=byte bajo del puntero, Y=byte alto. No necesita terminador cero.
SETTIM|$FFDB|Fija el reloj de 24 bits: A=byte bajo, X=medio, Y=alto.
SETTMO|$FFA2|Entrada de compatibilidad para timeout del bus. En la ROM C64 estándar no realiza una operación útil.
STOP|$FFE1|Comprueba STOP. Devuelve Z=1 si está pulsada; puede restaurar canales como parte del tratamiento de STOP.
TALK|$FFB4|Ordena transmitir al dispositivo IEC cuyo número está en A.
TKSA|$FF96|Envía dirección secundaria después de TALK; A contiene el comando, normalmente $60 OR secundaria.
UDTIM|$FFEA|Actualiza el reloj del sistema y el estado de STOP. Normalmente la llama la IRQ; no duplicarla sin motivo.
UNLSN|$FFAE|Envía UNLISTEN al bus serie para terminar la fase de escucha.
UNTLK|$FFAB|Envía UNTALK al bus serie para terminar la fase de transmisión.
VECTOR|$FF8D|Transfiere los vectores KERNAL de RAM: C=1 los copia al buffer X/Y; C=0 los instala desde ese buffer de 32 bytes.
''')
assert len(kernal)==39
for start,end in [(0,13),(13,26),(26,39)]:
    part=kernal[start:end]
    add('08 / ROM KERNAL: '+part[0][0]+' - '+part[-1][0],
        'Las 39 entradas públicas de la tabla KERNAL, ordenadas por nombre.',
        ['Rutina','Dirección','Para qué sirve / parámetros'],part,[65,57,WIDTH-122],notes=[
        'Los nombres son convenciones de documentación: Kick Assembler no define automáticamente CHROUT, GETIN, etc. Hay que definir esos símbolos o usar la dirección.',
        'Las llamadas ordinarias se hacen con jsr y regresan con rts. La ROM debe estar visible en el mapa de memoria; no asumir que A, X, Y o los flags se conservan salvo documentación explícita.',
        'Las rutinas de teclado, pantalla y reloj dependen del estado del KERNAL y, en varios casos, de su IRQ. GETIN lee el buffer; no explora por sí sola la matriz del teclado.',
        'La salida KERNAL de pantalla usa el editor de caracteres. No proporciona un motor de texto ni una rutina de borrado de bitmap.'
        ])

add('09 / ROM: uso práctico y entradas internas','Las direcciones internas siguientes son una selección, no una API pública ni un inventario de toda la ROM.',
 ['Entrada','Función / condición'],rows('''
CHROUT: A=$93|Con salida a pantalla, limpia caracteres y lleva el cursor al inicio. No borra 8000 bytes de bitmap.
CHROUT: A=$13|Lleva el cursor al inicio de la pantalla sin limpiarla.
CHROUT: A=$0D|Retorno de carro mediante el editor.
CHROUT: A=$11 / $91|Mueve el cursor abajo / arriba.
CHROUT: A=$1D / $9D|Mueve el cursor derecha / izquierda.
CHROUT: A=$12 / $92|Activa / desactiva caracteres en reverso.
$AB1E / STROUT|BASIC V2: imprime una cadena terminada en cero. A=byte bajo del puntero, Y=alto; usa el estado de BASIC.
$BDCD / LINPRT|BASIC V2: imprime un entero sin signo de 16 bits en decimal. A=byte alto, X=byte bajo.
$BDDD / FOUT|BASIC V2: convierte el acumulador flotante FAC a una cadena; devuelve el puntero en A (bajo) e Y (alto). Usa un buffer en la página de pila.
$E544|Editor: limpia la pantalla de caracteres y restablece su estado de líneas/cursor. Es una dirección interna; preferir CHROUT con $93.
$E566|Editor: lleva el cursor al inicio. Dirección interna; preferir CHROUT con $13 o PLOT.
'''),[122,WIDTH-122],notes=[
 'El KERNAL ocupa normalmente $E000-$FFFF; BASIC V2, $A000-$BFFF. Hay además código auxiliar de BASIC en la zona alta. No toda dirección dentro de una ROM es una entrada válida a una subrutina.',
 'Las rutinas internas pueden depender de variables en página cero, FAC, punteros y pila. Sus nombres varían entre listados. Para otras entradas, consultá el desensamblado enlazado en Fuentes.',
 ('CONTRATOS QUE CONVIENE RECORDAR',[
 ['Archivos','SETNAM y SETLFS preparan parámetros; OPEN abre; CHKIN/CHKOUT seleccionan canal; CHRIN/CHROUT transfieren; CLRCHN restaura; CLOSE cierra.'],
 ['Error de E/S','Comprobar C y A en las llamadas que documentan error por carry; READST obtiene otros bits de estado del canal. No todas las rutinas usan el mismo contrato.'],
 ['PLOT vs SCREEN','PLOT usa X=fila e Y=columna. SCREEN devuelve X=ancho e Y=alto. No intercambiarlos.'],
 ])
])

add('10 / Memoria y video: recordatorio','Direcciones útiles para este proyecto. La configuración del banco de memoria puede cambiar su interpretación.',
 ['Dirección / dato','Referencia rápida'],rows('''
$0000 / $0001|Dirección y datos del puerto del 6510; participan en la selección de RAM, ROM y E/S.
$0100-$01FF|Pila del procesador: 256 bytes. jsr, interrupciones y operaciones push/pull la utilizan.
$0400-$07E7|1000 celdas de pantalla en la configuración inicial. Caracteres en modo texto; colores en bitmap.
$07F8-$07FF|Punteros de sprites con pantalla en $0400. No son celdas visibles. Cambian al mover la memoria de pantalla.
$D000-$D00F|Coordenadas X bajas e Y de los ocho sprites, intercaladas.
$D010|Bit alto de X de cada sprite.
$D011|Control de video: bit 5 activa bitmap; bit 6 selecciona modo extendido. Bit 7 tiene distinta función al leer y escribir.
$D012|Lectura: línea raster baja. Escritura: comparador de IRQ raster bajo.
$D015|Habilita sprites: un bit por sprite.
$D016|Control horizontal y multicolor: bit 4 habilita multicolor.
$D017 / $D01D|Expansión vertical / horizontal de sprites.
$D018|Selecciona memoria de pantalla y fuente o bitmap dentro del banco VIC-II.
$D019 / $D01A|Estado/confirmación de interrupciones VIC-II y máscara de habilitación. En $D019 se escriben unos para reconocer eventos.
$D01B / $D01C|Prioridad respecto del fondo / multicolor de sprites.
$D01E / $D01F|Colisiones sprite-sprite / sprite-fondo. La lectura limpia los indicadores acumulados.
$D020 / $D021|Color del borde / primer color de fondo; usan los cuatro bits bajos.
$D025-$D026|Dos colores compartidos por sprites multicolor.
$D027-$D02E|Color individual de cada sprite.
$D800-$DBE7|RAM de color para las 1000 celdas; cuatro bits útiles por posición.
$DC00 / $DC01|Puertos CIA1: teclado y joysticks. Para leer matriz hay que configurar correctamente sus direcciones.
$DD00|Los dos bits bajos del puerto CIA2 seleccionan el banco VIC-II de 16 KiB, con codificación invertida.
Bitmap / sprite|Bitmap: 8000 bytes en un bloque alineado a 8 KiB. Sprite: 63 bytes de dibujo en un bloque alineado a 64 bytes.
'''),[115,WIDTH-115],notes=[
 'Bitmap hires: 320 x 200; cada bloque de 8 x 8 elige dos colores mediante los dos nibbles de su byte de pantalla. Bitmap multicolor: 160 x 200; cada par de bits elige entre cuatro colores.',
 'Precaución de lectura-modificación-escritura: $D011 leído devuelve el bit alto del raster actual, pero al escribir programa el comparador de IRQ. No todos los registros de hardware son RAM ordinaria.'
])

pages.append(dict(title='11 / Fuentes y alcance',subtitle='Referencia para C64 clásica y el ensamblador instalado en este proyecto.',sources=True))

c=canvas.Canvas(str(OUT),pagesize=A4,pageCompression=1)
c.setTitle('Opcodes C64 - Guía rápida de 6510, KERNAL y Kick Assembler 5.25')
c.setAuthor('Guía de consulta para el proyecto Snake C64')
c.setSubject('Mnemónicos, operadores, directivas, ROM y memoria - referencia en español')
y=0
def para(text,width=WIDTH,style='body',x=LEFT):
    global y
    p=Paragraph(text,styles[style]); _,h=p.wrap(width,1000)
    if y-h<43: raise RuntimeError(f'Overflow page {c.getPageNumber()} y={y} h={h}: {text[:80]}')
    p.drawOn(c,x,y-h); y-=h+7
def table(headers,data,widths):
    global y
    assert len(widths)==len(headers)
    for idx,row in enumerate([headers]+data):
        if len(row)!=len(widths): raise ValueError(row)
        ps=[]
        for col,(txt,width) in enumerate(zip(row,widths)):
            style='head' if idx==0 else ('mono' if col==0 else 'cell')
            p=Paragraph(escape(str(txt)),styles[style]); _,h=p.wrap(width-14,1000); ps.append((p,h))
        height=max(h for _,h in ps)+12
        if y-height<48: raise RuntimeError(f'Table overflow page {c.getPageNumber()}: {row}')
        c.setFillColor(NAVY if idx==0 else (LIGHT if idx%2 else colors.white))
        c.rect(LEFT,y-height,WIDTH,height,fill=1,stroke=0)
        x=LEFT
        for width,(p,h) in zip(widths,ps):
            p.drawOn(c,x+7,y-6-h); x+=width
        c.setStrokeColor(colors.HexColor('#DCE5EB')); c.setLineWidth(.3)
        c.line(LEFT,y-height,LEFT+WIDTH,y-height)
        y-=height
    y-=12
def title_small(text):
    global y
    y-=4
    para('<b>'+escape(text)+'</b>')

for num,page in enumerate(pages,1):
    c.bookmarkPage('p'+str(num))
    c.addOutlineEntry(page['title'],'p'+str(num),0,False)
    c.setFillColor(TEAL); c.rect(0,H-9,W,9,fill=1,stroke=0)
    c.setFillColor(MUTED); c.setFont('Bold',8)
    c.drawString(LEFT,H-30,'C64  /  REFERENCIA DE ESCRITORIO')
    c.setFillColor(NAVY); c.setFont('Bold',22)
    c.drawString(LEFT,H-62,page['title'])
    y=H-77
    para(escape(page['subtitle']),style='small')
    y-=8
    if page.get('cover'):
        para('Una guía de consulta en español para programar la Commodore 64 en assembler. Entradas breves, agrupadas por tema y ordenadas alfabéticamente cuando corresponde.')
        title_small('BUSCAR RÁPIDO')
        for pn,p in enumerate(pages[1:],2):
            label={3:'02 / Mnemónicos oficiales: adc - tya (pp. 3-5)',9:'06 / Directivas de Kick Assembler (pp. 9-11)',13:'08 / Las 39 rutinas KERNAL (pp. 13-15)'}.get(pn,p['title'])
            if pn in (4,5,10,11,14,15): continue
            para(f'<link href="#p{pn}" color="#007F82">{escape(label)}</link> <font color="#526276">/ página {pn}</font>')
        title_small('TRES CAPAS DIFERENTES')
        table(['Capa','Dónde actúa'],[
            ['Instrucción: lda, sta, bne','La ejecuta el 6510 mientras corre tu programa.'],
            ['Directiva: .byte, .fill, .for','La procesa Kick Assembler en Windows para construir el programa.'],
            ['Rutina: CHROUT, GETIN','Es código ya presente en ROM; tu programa lo llama con parámetros.'],
        ],[190,WIDTH-190])
        para('<b>Alcance:</b> los 56 mnemónicos oficiales del 6510, los no oficiales listados por Kick Assembler 5.25, sus operadores documentados, directivas y preprocesador; las 39 entradas públicas KERNAL y una selección explícita de entradas internas de ROM. No es un inventario de todos los puntos internos de BASIC/KERNAL.')
        para('Las formas de sintaxis son referencias aisladas. No incluye una implementación del juego ni modifica tu archivo main.asm.',style='small')
        para('Consulta con Ctrl+F, el índice enlazado o los marcadores del lector PDF. Edición: 6 de octubre de 2026.',style='small')
    elif page.get('sources'):
        title_small('BASE DOCUMENTAL')
        source_links=[
          ('Kick Assembler Reference Manual, Mads Nielsen','https://theweb.dk/KickAssembler/','Base principal: KickAssembler.pdf de tu proyecto. Capítulos 3-9, 10-14, 16-17 y apéndice A. Se cotejó el catálogo local, incluida .watch, que no figura en su tabla resumida.'),
          ('Manual HTML de Kick Assembler','https://theweb.dk/KickAssembler/webhelp/content/index.html','Para consultar parámetros completos, ejemplos de directivas y la biblioteca de funciones de script.'),
          ('Commodore 64 Programmer\'s Reference Guide: KERNAL','https://www.devili.iki.fi/Computers/Commodore/C64/Programmers_Reference/Chapter_5/page_272.html','Tabla original de las 39 entradas públicas. Las direcciones de esta guía corresponden a C64, no a C128 ni a otros modelos.'),
          ('KERNAL API: documentación y fuentes contrastadas','https://www.pagetable.com/c64ref/kernal/','Incluye la documentación original de Commodore, contratos y comentarios sobre las diferencias entre rutinas.'),
          ('ROM de la C64: listado y fuentes originales','https://www.pagetable.com/c64ref/c64disasm/','Para verificar entradas internas, registros de entrada, variables temporales y el flujo completo de BASIC/KERNAL.'),
          ('6502 Family CPU Reference','https://www.pagetable.com/c64ref/6502/','Consulta interactiva para bytes de opcode, ciclos y variantes. Seleccionar NMOS 6502/6510, no 65C02.'),
          ('Mapa de memoria C64','https://www.pagetable.com/c64ref/c64mem/','Ampliación de direcciones de RAM, ROM, VIC-II, SID y CIA.'),
        ]
        for label,url,desc in source_links:
            para('<b>'+escape(label)+'</b>')
            para('<link href="'+url+'" color="#007F82">'+escape(url)+'</link>',style='small')
            para(escape(desc),style='small')
        title_small('CÓMO USAR ESTA GUÍA')
        para('Los parámetros de ROM son un resumen operativo, no una lista completa de registros destruidos y efectos laterales. Para una llamada nueva, contrastá su contrato completo. Los modos de direccionamiento aparecen junto a cada mnemónico; el costo en ciclos depende del modo y, a veces, de cruces de página.')
        para('Las descripciones están redactadas para consulta rápida. Las extensiones exclusivas del 65C02/DTV y el inventario completo de métodos de script quedan fuera del alcance C64 de esta edición.')
    else:
        table(page['headers'],page['rows'],page['widths'])
        for note in page['notes']:
            if isinstance(note,tuple):
                title_small(note[0]); table(['Referencia','Descripción'],note[1],[135,WIDTH-135])
            else: para(escape(note),style='small')
    c.setStrokeColor(colors.HexColor('#CDD9E0')); c.line(LEFT,33,W-LEFT,33)
    c.setFont('Body',8); c.setFillColor(MUTED)
    c.drawString(LEFT,20,'6510 NMOS  |  Kick Assembler 5.25  |  Guía rápida')
    c.drawRightString(W-LEFT,20,f'{num:02d} / {len(pages):02d}')
    c.showPage()
c.save()
print(f'Created {OUT} ({len(pages)} pages)')
