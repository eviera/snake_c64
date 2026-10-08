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




    rts                     // return from subrutine, vuelve a BASIC
