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

// borrado de toda la pantalla. Son 1000 chars (40x25). 
    lda     #$20            // cargo espacio (screen code 32, hexa $20)
    ldx     #0              // inicio el indice del bucle

// borro los primeros 256+256+256 = 768
clean_screen:
    sta     $0400,x        // inicializo en la posicion 0 de pantalla
    sta     $0500,x        // inicializo en la pos 256
    sta     $0600,x        // inicializo en la 512
    inx
    bne     clean_screen   // aca salta cuando x que es de 8 bits da la vuelta completa y pasa de 255 a 0. Esto hace saltar el registro Z que queda en 1, y bne sale del bucle
// ahora borro las 1000-768 = 232 posiciones restantes
clean_screen_last_chars:
    sta     $0700,x       // x tiene que estar en 0
    inx
    cpx     #232
    bne     clean_screen_last_chars
    


    
    rts                     // return from subrutine, vuelve a BASIC
