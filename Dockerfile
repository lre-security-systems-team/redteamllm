FROM kalilinux/kali-rolling

RUN apt-get update && apt-get install -y curl

RUN apt-get update && apt-get install -y nmap curl

# Update and install Python and other dependencies
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip iputils-ping net-tools

# Install build via pip
RUN pip install build --break-system-packages

# Copy your project files
COPY . /redteam/
WORKDIR /redteam

# Build and install your package
RUN python3 -m build && pip install dist/*.whl --break-system-packages

CMD ["bash"]
