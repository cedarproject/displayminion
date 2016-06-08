# Render Quill's intermediate format into Kivy's obscure BBcode-ish markup (https://kivy.org/docs/api-kivy.uix.label.html#markup-text)

# TODO implement fill-in-the-blank lookahead/behind for lists, continuation for multi-style strings
def presentation_renderer(content, settings, args):
    output = ''

    fillin = 1
    fillin_cont = False
    list_line = 1
    
    for section in content['ops']:
        insert = section['insert']
        pre = ''
        
        for attr, value in section.get('attributes', {}).items():
            if attr == 'italic':
                insert = '[i]{}[/i]'.format(insert)
                
            elif attr == 'bold':
                insert = '[b]{}[/b]'.format(insert)
                
            elif attr == 'underline':
                insert = '[u]{}[/u]'.format(insert)
                
            elif attr == 'color':
                insert = '[color={}]{}[/color]'.format(value, insert)
            
            elif attr == 'strike':
                # Cedar currently hijacks strike tags for its fill-in feature
                if int(args.get('fillin')) < fillin:
                    insert = ''
                    
                fillin_cont = True
            
            elif attr == 'size':
                size = float(settings.get('presentations_font_size'))
                
                if value == 'small': size *= 0.75
                elif value == 'large': size *= 1.25
                elif value == 'huge': size *= 1.75
                
                insert = '[size={}]{}[/size]'.format(round(size), insert)
            
            if attr == 'indent':
                pre = '    ' * value + pre
            
            elif attr == 'list':
                if value == 'bullet':
                    pre += '  • '
                    
                elif value == 'ordered':
                    pre += '  {}. {}'.format(list_line, insert)
                    list_line += 1

        if '\n' in insert and not section.get('attributes', {}).get('list') == 'ordered':
            list_line = 1
        
        if fillin_cont and not section.get('attributes', {}).get('strike'):
            fillin_cont = False 
            fillin += 1
        
        i = output.rfind('\n')
        if not i == -1: output = output[:i+1] + pre + output[i+1:]
        
        output += insert
    
    return output
