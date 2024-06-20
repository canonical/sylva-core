package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: sylva-setup [command]")
		os.Exit(1)
	}

	command := os.Args[1]

	switch command {
	case "hello":
		fmt.Println("Hello man!")
	case "init":
		setupSylva()
	default:
		fmt.Println("Unknown command:", command)
	}
}

func setupSylva() {
	// Clone sylva-core repository
	cmd := exec.Command("git", "clone", "https://gitlab.com/sylva-projects/sylva-core.git")
	err := cmd.Run()
	if err != nil {
		fmt.Println("Failed to clone sylva-core repository:", err)
		os.Exit(1)
	}

	// Change directory to sylva-core
	err = os.Chdir("sylva-core")
	if err != nil {
		fmt.Println("Failed to change directory to sylva-core:", err)
		os.Exit(1)
	}

	// Prepare deployment values
	cmd = exec.Command("cp", "-r", "environment-values/kubeadm-capd/", "environment-values/my-kubeadm-capd")
	err = cmd.Run()
	if err != nil {
		fmt.Println("Failed to copy environment values:", err)
		os.Exit(1)
	}

	cmd = exec.Command("vim", "environment-values/my-kubeadm-capd/values.yaml")
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Println("Failed to modify environment values:", err)
		os.Exit(1)
	}

	// Setup Cluster Virtual IP
	cmd = exec.Command("bash", "-c", `
if ! docker network inspect kind > /dev/null 2>&1; then
  echo "Docker network 'kind' doesn't exist. Creating the network..."
  docker network create kind
fi

KIND_PREFIX=$(docker network inspect kind -f '{{ (index .IPAM.Config 0).Subnet }}')
CLUSTER_IP=$(echo $KIND_PREFIX | awk -F"." '{print $1"."$2"."$3".100"}')
echo $CLUSTER_IP
yq -i ".cluster_virtual_ip = \"$CLUSTER_IP\"" environment-values/my-kubeadm-capd/values.yaml
`)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Println("Failed to setup Cluster Virtual IP:", err)
		os.Exit(1)
	}

	// Verify virtual cluster IP
	cmd = exec.Command("yq", "e", ".cluster_virtual_ip", "environment-values/my-kubeadm-capd/values.yaml")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	err = cmd.Run()
	if err != nil {
		fmt.Println("Failed to verify virtual cluster IP:", err)
		os.Exit(1)
	}

	fmt.Println("Sylva setup completed successfully!")
}
