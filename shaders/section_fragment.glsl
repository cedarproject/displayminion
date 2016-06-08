$HEADER$

uniform float brightness;
uniform float adjust;
uniform int alpha_mask;

uniform float tex_x;
uniform float tex_y;
uniform float tex_width;
uniform float tex_height;

uniform float blend_top;
uniform float blend_bottom;
uniform float blend_left;
uniform float blend_right;

const float edge_blend_power = 1.0;

void main (void) {
    gl_FragColor = texture2D(texture0, tex_coord0);
    gl_FragColor *= vec4(brightness, brightness, brightness, 1.0);
    
    // Edge blending
    if (tex_coord0[0] > tex_x && tex_coord0[0] < blend_left + tex_x) {
        gl_FragColor[3] *= pow(1.0 / (blend_left / (tex_coord0[0] - tex_x)), edge_blend_power);
    }
    
    else if (tex_coord0[0] < tex_x + tex_width && tex_coord0[0] > tex_x + tex_width - blend_right) {
        gl_FragColor[3] *= pow(1.0 / (blend_right / ((tex_x + tex_width) - tex_coord0[0])), edge_blend_power);
    }
    
    else if (tex_coord0[1] > tex_y && tex_coord0[1] < blend_top + tex_y) {
        gl_FragColor[3] *= pow(1.0 / (blend_top / (tex_coord0[1] - tex_y)), edge_blend_power);
    }
    
    else if (tex_coord0[1] < tex_y + tex_height && tex_coord0[1] > tex_y + tex_height - blend_bottom) {
        gl_FragColor[3] *= pow(1.0 / (blend_bottom / ((tex_y + tex_height) - tex_coord0[1])), edge_blend_power);
    }
    
    
    // Color adjustment (for luma keying) and gamma correction
    for (int i = 0; i < 3; i++) {
        if (gl_FragColor[i] < adjust) {
            gl_FragColor[i] = adjust;
        }
    }
    
    
    // Alpha masking
    if (alpha_mask == 1) {
        gl_FragColor = vec4(gl_FragColor[3], gl_FragColor[3], gl_FragColor[3], gl_FragColor[3]);
    }
}
