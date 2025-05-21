from grpc_tools import protoc
import os
import re

def main():
    proto_file = 'proto/messages.proto'
    
    # Create generated directory if it doesn't exist
    os.makedirs('generated', exist_ok=True)
    
    # Generate Python code from proto file
    protoc.main([
        'grpc_tools.protoc',
        '-Iproto',
        '--python_out=generated',
        '--grpc_python_out=generated',
        proto_file
    ])
    
    # Create __init__.py in generated directory
    with open(os.path.join('generated', '__init__.py'), 'w') as f:
        pass
    
    # Fix imports in the generated _pb2_grpc.py file
    grpc_file = os.path.join('generated', 'messages_pb2_grpc.py')
    with open(grpc_file, 'r') as f:
        content = f.read()
    
    # Replace "import messages_pb2" with "from . import messages_pb2"
    fixed_content = re.sub(
        r'import messages_pb2 as messages__pb2',
        r'from . import messages_pb2 as messages__pb2',
        content
    )
    
    with open(grpc_file, 'w') as f:
        f.write(fixed_content)

if __name__ == '__main__':
    main()
    print("gRPC code generation complete!")
