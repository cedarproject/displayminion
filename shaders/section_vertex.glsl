$HEADER$

uniform mat4       uTransformMatrix;

void main(void) {
    gl_Position = uTransformMatrix * vec4(vPosition.xy, 0.0, 1.0);
    frag_color = color * vec4(1.0, 1.0, 1.0, opacity);
    tex_coord0 = vTexCoords0;
}
