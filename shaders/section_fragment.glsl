$HEADER$

uniform float brightness;
uniform float opacity;

uniform vec4 background;
uniform float adjust;

void main (void) {
    gl_FragColor = texture2D(texture0, tex_coord0);

/*    gl_FragColor *= vec4(brightness, brightness, brightness, opacity);
    
    for (int i = 0; i <= 2; i++) {
        if (gl_FragColor[i] - background[i] < adjust && gl_FragColor[i] - background[i] >= 0.0) {
            gl_FragColor[i] = background[i] + adjust;
        }
        
        else if (gl_FragColor[i] - background[i] > -adjust && gl_FragColor[i] - background[i] < 0.0) {
            gl_FragColor[i] = background[i] - adjust;
        }
    } */
}
