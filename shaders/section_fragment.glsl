$HEADER$

uniform float brightness;

/* uniform float blend_top;
uniform float blend_bottom;
uniform float blend_left;
uniform float blend_right; */

uniform float adjust;

void main (void) {
    gl_FragColor = texture2D(texture0, tex_coord0);
    gl_FragColor *= vec4(brightness, brightness, brightness, 1.0);
    
/*    if (tex_coord0[0] < blend_left) {
        gl_FragColor[3] *= 1.0 / (blend_left / tex_coord0[0]);
    } else if (tex_coord0[0] > blend_right) {
        gl_FragColor[3] *= 1.0 / (blend_right / (1.0 - tex_coord0[0]));
    } else if (tex_coord0[1] < blend_top) {
        gl_FragColor[3] *= 1.0 / (blend_top / tex_coord0[1]);
    } else if (tex_coord0[1] < blend_bottom) {
        gl_FragColor[3] *= 1.0 / (blend_bottom / (1.0 - tex_coord0[1]));
    } */
}
