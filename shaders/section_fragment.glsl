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

float f (float x) {
/*    if (x < 0.5) {
        return 0.25 * pow(2.0 * x, 3.0);
    } else {
       return 1.0 - 0.5 * pow(2.0 * (1.0 - x), 3.0);
    } */
    return x;
}

void main (void) {
    gl_FragColor = texture2D(texture0, tex_coord0);
    gl_FragColor *= vec4(brightness, brightness, brightness, 1.0);
    
    // Edge blending
    if (tex_coord0[0] >= tex_x && tex_coord0[0] <= blend_left + tex_x) {
        gl_FragColor[3] *= f(1.0 / (blend_left / (tex_coord0[0] - tex_x)));
    }
    
    else if (tex_coord0[0] <= tex_x + tex_width && tex_coord0[0] > tex_x + tex_width - blend_right) {
        gl_FragColor[3] *= f(1.0 / (blend_right / ((tex_x + tex_width) - tex_coord0[0])));
    }
    
    else if (tex_coord0[1] > tex_y && tex_coord0[1] < blend_top + tex_y) {
        gl_FragColor[3] *= f(1.0 / (blend_top / (tex_coord0[1] - tex_y)));
    }
    
    else if (tex_coord0[1] < tex_y + tex_height && tex_coord0[1] > tex_y + tex_height - blend_bottom) {
        gl_FragColor[3] *= f(1.0 / (blend_bottom / ((tex_y + tex_height) - tex_coord0[1])));
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
