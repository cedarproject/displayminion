import mistune

# Render Markdown into Kivy's obscure BBcode-ish markup (https://kivy.org/docs/api-kivy.uix.label.html#markup-text)
class PresentationRenderer(mistune.Renderer):
    def __init__(self, *args, **kwargs):
        # TODO font etc. settings
        self.settings = kwargs['settings']
        del kwargs['settings']

        super(PresentationRenderer, self).__init__(*args, **kwargs)
    
    def paragraph(self, text):
        return '{}\n'.format(text)
        
    def header(self, text, level, raw = None):
        size = float(self.settings.get('presentations_font_size', 2)) # TODO actual defaults!
        if level == 1: size *= 2
        elif level == 2: size *= 1.5
        elif level == 3: size *= 1.17
        
        return '[size={}]{}[/size]\n'.format(str(round(size)), text)
        
    def list(self, body, ordered = True):
        # TODO settings for list indent size?
        lines = body.split('\n')
        output = ''
        
        for line, n in zip(lines, enumerate(lines)):
            if ordered:
                output += '    {}. {}\n'.format(str(n + 1), line)
            else:
                output += '    • {}\n'.format(line)

        return output
        
    def list_item(self, text):
        return '{}\n'.format(text)
        
    def codespan(self, text):
        # Cedar hijacks inline code spans for its fill-in-the-blank feature
        # TODO fill-in-the-blank!
        
        return '`{}`'.format(text)
    
    def emphasis(self, text):
        return '[i]{}[/i]'.format(text)
        
    def double_emphasis(self, text):
        return '[b]{}[/b]'.format(text)
        
    def linebreak(self):
        return '\n'
    
    def newline(self):
        return '\n'
        
    def strikethrough(self, text):
        # Hijacked, now it's underline
        return '[u]{}[/u]'.format(text)
        
    def text(self, text):
        return text
