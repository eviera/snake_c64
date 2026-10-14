* = $C000               // directiva de inicio, indica en que region de memoria se ejecuta el codigo


    //Borde negro
    lda     #$00             // carga el numero 0 en A
    sta     $D020           // setea el borde en el color guardado en A

    //Fondo verde
    lda     #$05
    sta     $D021           // color de fondo

    //pongo una A en la primera fila/columna del modo texto
    // lda     #$01            // La A es $01 en los screen codes (no es ASCII)
    // sta     $0400           // direccion de memoria de la pantalla para los screen codes (texto de 40x25)


/* 
    //bucle para limpiar la primer fila
    lda     #$20            // cargo espacio (screen code 32, hexa $20)
    ldx     #0              // inicio el indice del bucle
clean_start:
    sta     $0400,x
    inx                     // incrementa x
    cpx     #40             // comparo x con la ultima columna, 39 (me paso uno porque incremento antes de comparar)
    bne     clean_start     // salto al comienzo del bucle si son distintos  (BNE	Branch if not equal)

*/

/*
// borrado de toda la pantalla de texto. Son 1000 chars (40x25). 
    lda     #$20            // cargo espacio (screen code 32, hexa $20)
    ldx     #0              // inicio el indice del bucle

// borro los primeros 256+256+256 = 768
clean_text_screen:
    sta     $0400,x        // inicializo en la posicion 0 de pantalla
    sta     $0500,x        // inicializo en la pos 256
    sta     $0600,x        // inicializo en la 512
    inx
    bne     clean_text_screen   // aca salta cuando x que es de 8 bits da la vuelta completa y pasa de 255 a 0. Esto hace saltar el registro Z que queda en 1, y bne sale del bucle
// ahora borro las 1000-768 = 232 posiciones restantes
clean_text_screen_last_chars:
    sta     $0700,x       // x tiene que estar en 0
    inx
    cpx     #232
    bne     clean_text_screen_last_chars
*/   


// hago algo parecido a borrar la pantalla de texto, pero esta vez asignando los colores que quiero para el modo bitmap
    lda     #$50            // cargo el hexa $50 que corresponde al binario 0101 0000. El nibble alto indica el color para el pixel 1 (verde en este caso 0101), y el nibble bajo el color para el pixel 0 (negro 0000)
    ldx     #0              // inicio el indice del bucle

// seteo primeros 256+256+256 = 768
set_bitmap_colors:
    sta     $0400,x        // inicializo en la posicion 0 de pantalla
    sta     $0500,x        // inicializo en la pos 256
    sta     $0600,x        // inicializo en la 512
    inx
    bne     set_bitmap_colors   // aca salta cuando x que es de 8 bits da la vuelta completa y pasa de 255 a 0. Esto hace saltar el registro Z que queda en 1, y bne sale del bucle
// ahora seteo las 1000-768 = 232 posiciones restantes
set_bitmap_colors_last_bytes:
    sta     $0700,x       // x tiene que estar en 0
    inx
    cpx     #232
    bne     set_bitmap_colors_last_bytes



// borrado de toda la pantalla bitmap. Son 8000 bytes. Vamos a rellenar con 0s (de $2000 a $3F3F)
// primero seteo en la pagina cero (zero page, primera pagina y es especial) el valor $2000 que es donde quiero que apunte la primer direccion
    lda     #$00    
    sta     $FB             // en $00FB va el byte bajo 00
    lda     #$20            // en $00FC va el byte alto 20... quedando guardado 0020, que se lee como 2000 (little endian)
    sta     $FC

    lda     #$00            // lleno con ceros
    ldx     #31             // cantidad de bloques de 256 a borrar = 31*256 = 7936 (nos quedan luego 64 bytes mas por borrar para llegar a los 8000 bytes totales de la pantalla bitmap)
    ldy     #0              // inicio bucle

clear_bitmap:
    sta     ($FB),y         // guarda el valor de A ($0 en este caso), en donde direccione el puntero de 16 bits apuntado por las direcciones de $00FB y $00FC (00 y 20, que se lee como $2000) sumado el valor de y, entonces hace $2000+0, $2000+1, etc, hasta $2000+255
    iny                     // incrementa y
    bne     clear_bitmap    // salta a clear_bitmap si y != 0
    inc     $FC             // incrementa $FC para apuntar al proximo bloque de 256 bytes, arrancando en $2100
    dex                     // decrementa el contador de los 31 bloques
    bne     clear_bitmap    // repito hasta que x llegue a 0
clear_last_64_bytes_bitmap:
    sta     ($FB),y
    iny
    cpy     #64
    bne     clear_last_64_bytes_bitmap

/* 
    Colores, para bailar este twist

    Parte del byte	Función
    Bits 7–4, nibble alto	Color de los píxeles cuyo bit es 1
    Bits 3–0, nibble bajo	Color de los píxeles cuyo bit es 0

    Un nibble es medio byte: 4 bits. Puede representar valores de 0 a 15, justo los 16 colores de la C64.
    Por ejemplo, $25 selecciona rojo (2) para los bits 1 y verde (5) para los bits 0. En este modo, esos colores los determina cada celda; $D021 no decide el fondo del bitmap.    
    
                    $25 es en binario 0010 0101
                    Nibble Alto     Nibble Bajo
                    0010            0101
                    Dec 2 - Rojo    Dec 5 - Verde

                    Color	    Dec	Hex	Nibble
                    Negro	    0	$00	0000
                    Blanco	    1	$01	0001
                    Rojo	    2	$02	0010
                    Cian	    3	$03	0011
                    Violeta	    4	$04	0100
                    Verde	    5	$05	0101
                    Azul	    6	$06	0110
                    Amarillo    7	$07	0111
                    Naranja	    8	$08	1000
                    Marrón	    9	$09	1001
                    Rojo claro	10	$0A	1010
                    Gris oscuro	11	$0B	1011
                    Gris medio	12	$0C	1100
                    Verde claro	13	$0D	1101
                    Azul claro	14	$0E	1110
                    Gris claro	15	$0F	1111
                

    -----------------------------------------------------------------------------------------------------------------------------------------
    RESUMEN
    -------
    $2000 x 8000 bytes, pixeles
    $0400 x 1000 bytes, colores de bloques de 8x8 (2 colores por bloque, uno para los pixles 0, y otro para los pixeles 1)
    -----------------------------------------------------------------------------------------------------------------------------------------

    En bitmap hires, la imagen tiene 320 × 200 píxeles y se construye combinando dos zonas de memoria: los dibujos de los píxeles y sus colores.
    Las direcciones que elegimos son configurables; para nuestro proyecto vamos a usar estas:
    Zona	            Direcciones	        Tamaño	        Contenido
    Bitmap (pixeles)    $2000–$3F3F	        8000 bytes	    Un bit por píxel
    Colores del bitmap	$0400–$07E7	        1000 bytes	    Dos colores por bloque de 8 × 8 píxeles (con colores para el 0 y para el 1 en los nibbles del byte)

    La pantalla se divide en 40 × 25 bloques de 8 × 8 píxeles. Cada bloque ocupa ocho bytes, uno por fila:
    Dirección	Qué representa
    $2000	Primera fila del primer bloque
    $2001	Segunda fila del primer bloque
    …	…
    $2007	Última fila del primer bloque
    $2008	Primera fila del segundo bloque, a la derecha
    $200F	Última fila del segundo bloque

    Dentro de cada byte, el bit 7 corresponde al píxel izquierdo y el bit 0 al derecho.
    Un byte $80, es decir 10000000, selecciona el color 1 para el primer píxel y el color 0 para los otros siete. Esos nombres indican las dos opciones del bloque; no significan necesariamente blanco y negro.

    La memoria en $0400: cuáles son esos colores
    Cada bloque tiene un byte que define sus dos colores:
    Dirección	Bloque que colorea
    $0400	    Primer bloque: bitmap $2000–$2007
    $0401	    Segundo bloque: bitmap $2008–$200F
    $0402	    Tercer bloque: bitmap $2010–$2017
    

    Así, con $80 en $2000 y $16 en $0400, la primera fila del primer bloque muestra un píxel blanco seguido de siete azules. Los ocho bytes de ese bloque comparten esos mismos dos colores.

    Los registros que seleccionan esa distribución
    Registro	    Función
    $DD00	        Selecciona el banco de 16 KiB que ve el VIC-II; usaremos el inicial, $0000–$3FFF.
    $D018	        Dentro de ese banco, selecciona dónde están el bitmap y la memoria de pantalla usada para sus colores.
    $D011, bit 5	Activa el modo bitmap. Su bit 6 debe estar en cero para bitmap estándar.
    $D016, bit 4	Debe estar en cero para hires; en uno selecciona multicolor.
    $D020	        Sigue controlando el color del borde.


*/

/*
// prueba de dibujar una linea vertical en el primer bloque
    lda     #$80            // $80 es 1000 0000, asi que queda una linea a la izquierda
    ldx     #0              // inicio el indice del bucle
loop_linea:
    sta     $2000,x
    inx
    cpx     #8
    bne     loop_linea
*/
    

// Vamos a seleccionar $2000 como ubicación del bitmap, poniendo el bit 3 de $D018 en 1. La máscara es 00001000, o $08
    lda     $D018           // Primero leo el contenido de $D018 en el registro A
    ora     #%00001000      // Oreo el bit 3 para prenderlo ($08)
    sta     $D018           // Guardo el valor oreado en $D018
// Ahora a setear el modo bitmap hires poniendo el 1 el bit 5 de $D011
    lda     $D011           // Primero leo el contenido de $D011 en el registro A
    ora     #%00100000      // Oreo el bit 5 para prenderlo 
    sta     $D011           // Guardo el valor oreado en $D011


// prueba de dibujar un cuadrado solido, teniendo su direccion apuntada por $00FB $00FC
// lo seteo en el primer lugar $2000 (fila 0, columna 0)
    lda     #$00    
    sta     $FB             // en $00FB va el byte bajo 
    lda     #$20            // en $00FC va el byte alto 
    sta     $FC

    lda     #$FF            // $FF es 1111 1111, asi que queda una todo solido
    jsr     fn_dibujar_bloque




// inicializaciond de variables
    lda     #0
    sta     fila
    sta     columna
    lda     #100
    sta     pasos           // abajo esta declarada la variable pasos

loop_bloques_prueba:

// espero por la tecla
    jsr     fn_getkey       
    
// analizo la tecla presionada
/*
    Q $51
    A $41
    O $4F
    P $50
*/    
    lda     tecla
    cmp     #$51         // Q
    beq     key_up
    cmp     #$41         // A
    beq     key_down
    cmp     #$4F         // O
    beq     key_left
    cmp     #$50         // P
    beq     key_right
    
key_up:
    // chequeo que no se quiera mover arriba de al fila 0
    lda     fila
    cmp     #0
    beq     loop_bloques_prueba
    dec     fila

    // borro el bloque original antes de moverme
    lda     #$00            
    jsr     fn_dibujar_bloque

    // le resto 320 bytes (40x8 una fila)
    sec                     
    lda     $FB             
    sbc     #$40            
    sta     $FB             
    lda     $FC             
    sbc     #$01            
    sta     $FC             
    jmp     dibujar_bloque_solido

key_down:
    // chequeo que no se quiera mover abajo de la fila 24
    lda     fila
    cmp     #24
    beq     loop_bloques_prueba
    inc     fila

    // borro el bloque original antes de moverme
    lda     #$00            
    jsr     fn_dibujar_bloque

    // sumo resto 320 bytes (40x8 una fila)
    clc                     
    lda     $FB             
    adc     #$40           
    sta     $FB             
    lda     $FC             
    adc     #$01            
    sta     $FC             
    jmp     dibujar_bloque_solido

key_left:
    // chequeo que no se quiera mover antes de la columna  0
    lda     columna
    cmp     #0
    beq     loop_bloques_prueba
    dec     columna

    // borro el bloque original antes de moverme
    lda     #$00            
    jsr     fn_dibujar_bloque

    // quiero restar $2200 - $08 para mover el cuadrado uno a la izquierda, usando acarreo y cambiando el puntero $FB/$FC
    // La instrucción es sbc (Subtract with Carry), pero el acarreo funciona así:
    // A = A − operando − (1 − C)
    // Por eso, antes de empezar una resta usamos sec, que pone C en 1: así no se descuenta una unidad adicional (porque queda A = A − operando − (1 − 1)).
    // | Operación                              | Resultado     | Acarreo           |
    // | Bajo: `$00 − $08`, sin préstamo previo | `$F8`         | 0: hubo préstamo  |
    // | Alto: `$22 − $00 − 1`                  | `$21`         | 1                 |
    sec                     // seteo el acarreo para lograr el '1 - 1'
    lda     $FB             // cargo el byte bajo que ya tenia en $00FB
    sbc     #$08            // le resto 8 (lo deja dentro de A, y ademas apaga el acarreo si se paso... funciona al reves que la suma, porque sbc hace A = A − operando − (1 − C))
    sta     $FB             // guardo el resultado de la suma en $00FB, el byte bajo
    lda     $FC             // cargo el byte alto que ya tenia en $00FC
    sbc     #$00            // resto cero, mas (menos) el carry
    sta     $FC             // guardo el resultado en el byte alto
    jmp     dibujar_bloque_solido


key_right:
    // chequeo que no se quiera mover despues de la columna 40
    lda     columna
    cmp     #39
    beq     loop_bloques_prueba
    inc     columna

    // borro el bloque original antes de moverme
    lda     #$00            
    jsr     fn_dibujar_bloque

    // quiero sumar $21F8 + $08 para mover el cuadrado uno a la derecha, usando acarreo y cambiando el puntero $FB/$FC
    // | Operación             | Resultado guardado | Acarreo   |
    // | Bajo: `$F8 + $08 + 0` | `$00`              | 1         |   
    // | Alto: `$21 + $00 + 1` | `$22`              | 0         |
    clc                     // limpio acarreo
    lda     $FB             // cargo el byte bajo que ya tenia en $00FB
    adc     #$08            // le sumo 8 (lo deja dentro de A, y ademas prende el acarreo porque se paso)
    sta     $FB             // guardo el resultado de la suma en $00FB, el byte bajo
    lda     $FC             // cargo el byte alto que ya tenia en $00FC
    adc     #$00            // sumo cero, mas el carry, lo que lo va a llevar a $22
    sta     $FC             // guardo el resultado en el byte alto
    jmp     dibujar_bloque_solido


dibujar_bloque_solido:
    lda     #$FF            // $FF es 1111 1111, asi que queda una todo solido
    jsr     fn_dibujar_bloque

    dec     pasos
    beq     loop_infinito           // no puedo hacer aca un bne hacia loop_bloques_prueba como quisiera porque esta muy lejos (solo salta 256 direcciones)
    jmp     loop_bloques_prueba


    // rts                     // return from subrutine, vuelve a BASIC
loop_infinito:
    jmp     loop_infinito



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

/*
    subrutina de dibujo un cuadrado solido, teniendo su direccion apuntada por $00FB $00FC
    parametros:
       A           representa una linea en el bloque ($00 nada, $FF toda llena)
       $00FB       tiene cargado el byte bajo a dibujar de las direcciones de la pantalla bitmap (8000 bytes totales desde $2000)
       $00FC       tiene cargado el byte alto
        
*/
fn_dibujar_bloque:
    ldy     #0              // inicio el indice del bucle
loop_linea:
    sta     ($FB),y         // este modo de direccionamiento solo funciona con y
    iny
    cpy     #8
    bne     loop_linea
    rts                     // return


/* 
    subrutina de espera de 255x255 loops
fn_loop_espera:
    ldx     #255
loop_x:
    ldy     #255
loop_y:
    dey
    bne     loop_y
    dex
    bne     loop_x
    rts
*/

/*
    espera por un caracter y lo devuelve en A
    Q $51
    A $41
    O $4F
    P $50
*/
fn_getkey:
    jsr     $FFE4           // devuelve en A inmediatamente el valor que haya en el buffer de teclado (en PETSCII), o 0 si no hay nada
    // salgo si es alguna de las teclas conocidas, sino, vuelvo a leer
    cmp     #$51            
    beq     salida
    cmp     #$41
    beq     salida
    cmp     #$4F
    beq     salida
    cmp     #$50
    beq     salida
    jmp     fn_getkey       
salida:
    sta     tecla           // guardo la tecla en el byte tecla
    rts    




pasos:      .byte   0
tecla:      .byte   0
fila:       .byte   0
columna:    .byte   0