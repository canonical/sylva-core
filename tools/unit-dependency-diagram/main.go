package main

import (
	"flag"
	"fmt"
	"os"
)

func write(diagramText []string, diagramName string) {
	// source: https://golangbot.com/write-files/#writing-strings-line-by-line-to-a-file
	file, err := os.Create(diagramName)
	if err != nil {
		fmt.Println(err)
		file.Close()
		return
	}

	for _, line := range diagramText {
		fmt.Fprintln(file, line)
		if err != nil {
			fmt.Println(err)
			return
		}
	}

	err = file.Close()
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Println("file " + diagramName + " written successfully")
}

// define a custom flag type for string slices to get skipUnit input
type stringSliceValue []string

// implement the flag.Value interface methods
func (s *stringSliceValue) String() string {
	return fmt.Sprintf("%v", *s)
}

func (s *stringSliceValue) Set(value string) error {
	*s = append(*s, value)
	return nil
}

func main() {
	/*
		Can be run as:
		    $ cd tools/unit-dependency-diagram
			$ go run . --allFlavors true --skipUnit root-dependency-1 --skipUnit management-flag // generates charts/sylva-units/docs/unit-dependency-diagrams/{bootstrap,management,workload}-cluster.md
		or
		    $ GOOS=linux GOARCH=amd64 go build -o dependaview
			$ ./tools/unit-dependency-diagram/dependaview --suPath charts/sylva-units --clusterType workload --clusterFlavor rke2-capo --skipUnit root-dependency-1 // displays mermaid syntax for workload cluster dependencies of an rke2-capo deployment
	*/

	allFlavors := flag.Bool("allFlavors", false, "boolean conditioning creation of diagrams for all sylva environment-values flavors")
	suPath := flag.String("suPath", "../../charts/sylva-units/", "relative path to sylva-units helm chart")
	clusterType := flag.String("clusterType", "bootstrap", "bootstrap|management|workload")
	clusterFlavor := flag.String("clusterFlavor", "rke2-capo", "{kubeadm,rke2}-{capd,capo,capv} rke2-{capm3,capm3-virt}")
	// define a flag for the input list of skipUnits
	var skipUnits []string
	flag.Var((*stringSliceValue)(&skipUnits), "skipUnit", "list of units to be skipped from the diagram computation, each such unit provided with --skipUnit <ks name>")

	flag.Parse()

	// transform the slice of skipUnit to a map, which is more efficient for the extractDependency() function
	skipUnitsMap := make(map[string]bool)
	for _, skipUnit := range skipUnits {
		skipUnitsMap[skipUnit] = true
	}

	if bool(*allFlavors) {
		for _, clusterType := range []string{"bootstrap", "management", "workload"} {
			diagramText := make([]string, 0, 2000)
			var mermaidTheme string
			switch clusterType {
			case "bootstrap":
				mermaidTheme = "neutral"
			case "management":
				mermaidTheme = "forest"
			case "workload":
				mermaidTheme = "dark"
			}
			diagramText = append(diagramText, "## [Kustomization dependencies](https://fluxcd.io/flux/components/kustomize/kustomizations/#dependencies) diagrams")
			diagramText = append(diagramText, "")
			diagramText = append(diagramText, "Following diagrams were created using [tools/unit-dependency-diagram](../../../../tools/unit-dependency-diagram) and calling [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) for SVG transformation.")
			diagramText = append(diagramText, "")
			diagramText = append(diagramText, "<Tabs groupId=\"flavor-tabs\">")
			diagramText = append(diagramText, "")
			for _, clusterFlavor := range []string{"kubeadm-capd", "kubeadm-capo", "kubeadm-capv", "rke2-capd", "rke2-capo", "rke2-capv", "rke2-capm3", "rke2-capm3-virt"} {
				diagramText = append(diagramText, "### "+clusterFlavor)
				diagramText = append(diagramText, "")
				diagramText = append(diagramText, "<TabItem value=\""+clusterFlavor+"\" label='"+clusterType+" cluster for "+clusterFlavor+" deployment'>")
				diagramText = append(diagramText, "")
				diagramText = append(diagramText, clusterType+" cluster for "+clusterFlavor+" deployment:")
				diagramText = append(diagramText, "")
				diagramText = append(diagramText, "```mermaid")
				diagramText = append(diagramText, "%%{init: {'theme': '"+mermaidTheme+"'} }%%", "graph TD;")
				diagramText = append(diagramText, extractDependency(string(*suPath), clusterType, clusterFlavor, skipUnitsMap)...)
				diagramText = append(diagramText, "```")
				diagramText = append(diagramText, "")
				diagramText = append(diagramText, "</TabItem>")
				diagramText = append(diagramText, "")
			}
			diagramText = append(diagramText, "</Tabs>")
			write(diagramText, "docs/unit-dependency-diagrams/"+clusterType+"-cluster.md")
		}
	} else {
		diagramText := make([]string, 0, 2000)
		diagramText = append(diagramText, "%%{init: {'theme': 'forest'} }%%", "graph TD;")
		diagramText = append(diagramText, extractDependency(string(*suPath), string(*clusterType), string(*clusterFlavor), skipUnitsMap)...)
		fmt.Println("\nThe mermaid syntax (can be dumped in https://mermaid.live/edit) for an " + string(*clusterFlavor) + " " + string(*clusterType) + " is:")
		for _, line := range diagramText {
			fmt.Println(line)
		}
	}
}
