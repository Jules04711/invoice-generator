# Invoice Generator - Portainer Deployment Guide

## Prerequisites
- Portainer installed and running
- Docker installed on your server
- Git access to the repository

## Deployment Options

### Option 1: Using Docker Compose (Recommended)

1. **Build and push the image first:**
   ```bash
   # Login to Docker Hub
   docker login
   
   # Build and push the image
   ./build-and-push.sh
   ```

2. **In Portainer:**
   - Go to **Stacks** in the left sidebar
   - Click **Add stack**
   - Give it a name: `invoice-generator`
   - Copy the contents of `docker-compose.yml` into the web editor
   - Set environment variables (optional):
     - `USERNAME`: Your desired username
     - `PASSWORD`: Your desired password
   - Click **Deploy the stack**

3. **Access the application:**
   - The app will be available at `http://your-server-ip:8501`
   - Login with:
     - Username: `jules04711`
     - Password: `Marti9ja!`

### Option 2: Using Portainer's Container Management

1. **Build the image:**
   - In Portainer, go to **Images**
   - Click **Build a new image**
   - Set the name: `invoice-generator:latest`
   - Upload your project files or use a Git repository URL
   - Click **Build the image**

2. **Create a container:**
   - Go to **Containers**
   - Click **Add container**
   - Set the following:
     - **Name**: `invoice-generator`
     - **Image**: `invoice-generator:latest`
     - **Port mapping**: `8501:8501`
     - **Environment variables**:
       - `USERNAME=jules04711`
       - `PASSWORD=Marti9ja!`
   - Click **Deploy the container**

## Environment Variables

The application uses a `.env` file for secure credential management:

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the credentials:**
   ```bash
   nano .env
   ```
   
   Update with your secure credentials:
   ```env
   USERNAME=your_secure_username
   PASSWORD=your_strong_password
   ```

**Security Benefits:**
- Credentials are not hardcoded in Docker files
- `.env` file is excluded from Git (in `.gitignore`)
- Easy to change credentials without rebuilding containers
- Follows security best practices

## Security Considerations

1. **Change default credentials** in the environment variables
2. **Use HTTPS** by setting up a reverse proxy (nginx/traefik)
3. **Restrict access** using firewall rules
4. **Regular updates** - pull the latest image periodically

## Troubleshooting

### Container won't start:
- Check logs: `docker logs invoice-generator`
- Verify port 8501 is not in use
- Ensure all files are copied correctly

### Can't access the application:
- Verify the container is running: `docker ps`
- Check port mapping: `docker port invoice-generator`
- Test connectivity: `curl http://localhost:8501`

### Login issues:
- Verify environment variables are set correctly
- Check the `.env` file if using one
- Restart the container after changing credentials

## Updates

To update the application:

1. **Pull the latest code:**
   ```bash
   git pull origin main
   ```

2. **Rebuild and restart:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Backup

The application doesn't store persistent data by default. If you need to backup any custom configurations, consider:

1. **Volume mounting** for persistent data
2. **Database integration** for user management
3. **External storage** for generated invoices

## Support

For issues or questions:
- Check the GitHub repository: https://github.com/Jules04711/invoice-generator
- Review the application logs in Portainer
- Ensure all dependencies are properly installed 