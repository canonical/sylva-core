package main

import (
	"fmt"
	"log"
	"os"
	"strings"

	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/serializer"

	"github.com/bitfield/script"
	kustomizev1 "github.com/fluxcd/kustomize-controller/api/v1"
)

var (
	// source: https://www.reddit.com/r/golang/comments/12rm094/comment/jgvxttj/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
	Scheme = runtime.NewScheme()
	Codecs = serializer.NewCodecFactory(Scheme)
)

func RemoveIndex(s []string, index int) []string {
	if index == (len(s) - 1) {
		return s[:index]
	} else {
		return append(s[:index], s[index+1:]...)
	}
}

func extractDependency(suPath string, clusterType string, clusterFlavor string, skipUnits map[string]bool) []string {
	// register the imported kubernetes type, to unmarshall slice of bytes to Kustomization.kustomize.toolkit.fluxcd.io
	kustomizev1.AddToScheme(Scheme)

	diagramText := make([]string, 0, 500)

	// source: https://pkg.go.dev/github.com/bitfield/script#Pipe.String
	// helmTemplate, err := script.Exec("helm template ../../charts/sylva-units/ --values ../../charts/sylva-units/values.yaml --values ../../charts/sylva-units/management.values.yaml --values ../../charts/sylva-units/bootstrap.values.yaml -s templates/units.yaml").String()

	var clusterTypeValues string
	clusterFlavorValues := " --values ../../environment-values/" + clusterFlavor + "/values.yaml" + " --values ../../environment-values/" + clusterFlavor + "/secrets.yaml"
	switch clusterType {
	case "bootstrap":
		clusterTypeValues = " --values management.values.yaml --values bootstrap.values.yaml"
	case "management":
		clusterTypeValues = " --values management.values.yaml"
	case "workload":
		clusterTypeValues = " --values workload-cluster.values.yaml"
		clusterFlavorValues = clusterFlavorValues + " --values ../../environment-values/workload-clusters/" + clusterFlavor + "/values.yaml" + " --values ../../environment-values/workload-clusters/" + clusterFlavor + "/secrets.yaml" + " --values test-values/workload-cluster/shared-settings-mock.values.yaml"
	default:
		fmt.Println("Unknown sylva cluster type")
	}

	// no way to run script.Exec() from different dir: https://github.com/bitfield/script/issues/112
	// os.Chdir() is system wide, both script.Exec() and os.Create() for writing to file change dir
	os.Chdir(suPath)
	helmArg := " . --values values.yaml" + clusterTypeValues + clusterFlavorValues + " -s templates/units.yaml"
	fmt.Println("\n Parsing output of: \n\t" + "helm template" + helmArg)
	helmTemplate, err := script.Exec("helm template" + helmArg).String()

	// helmTemplate, err := script.Exec("helm template . --values values.yaml --values management.values.yaml --values bootstrap.values.yaml -s templates/units.yaml").Stdout()
	if err != nil {
		panic(err)
	}
	// split the YAML data from helm template into individual Kubernetes manifests
	// by checking for "---" appearing after a newline character
	manifests := strings.Split(string(helmTemplate), "\n---")

	// a map of key unit name and value Kustomization name
	ksUnitMap := make(map[string]string)

	// parse each Kubernetes manifest
	for _, manifest := range manifests {
		manifestByteArray := []byte(manifest)
		// parse the YAML into a custom struct
		obj, _, err := Codecs.UniversalDeserializer().Decode(manifestByteArray, nil, nil)

		if err != nil {
			log.Println(fmt.Sprintf("Error while decoding YAML object. Err was: %s", err))
			continue
		}

		// process the parsed manifest
		// fmt.Println(reflect.TypeOf(obj)) // *v1.Kustomization

		// obj holds the decoded Kubernetes object, but its type is runtime.Object
		// which is an interface representing any Kubernetes API object.
		// we need to assert obj to type *v1.Kustomization
		kustomization, ok := obj.(*kustomizev1.Kustomization)
		if !ok {
			fmt.Println("Error: Failed to assert obj to *v1.Kustomization")
			continue
		}
		// get the unit name (ks.metadata.name can be different than ks.metadata.labels."sylva-units.unit")
		// and save it in a map with Kustomization name as key, when the unit name is different
		unitName := kustomization.Labels["sylva-units.unit"]
		if unitName != kustomization.Name {
			ksUnitMap[kustomization.Name] = unitName
		}

		if skipUnits[unitName] {
			fmt.Println("Kustomization " + kustomization.Name + " (produced by unit " + unitName + ") is skipped from the diagram as dependent unit")
			continue
		} else {
			fmt.Println("Parsing Kustomization " + kustomization.Name + " (produced by unit " + unitName + ") for elements of ks.spec.dependsOn")
			for _, dependencyKs := range kustomization.Spec.DependsOn {
				// fmt.Println(reflect.TypeOf(dependencyKs)) // meta.NamespacedObjectReference
				// fmt.Printf("%s\n", dependencyKs.Name)
				diagramText = append(diagramText, "  "+dependencyKs.Name+" --> "+kustomization.Name)
			}
		}
	}
	for ksName := range ksUnitMap {
		for i, line := range diagramText {
			// if one of the Kustomization names for which the unit name is different was used in diagramText elements
			// replace one occurence in that element with the unit name
			if strings.Contains(line, ksName) {
				diagramText[i] = strings.Replace(line, ksName, ksUnitMap[ksName], 1)
			}
		}
	}
	for _, line := range diagramText {
		fmt.Println(line)
	}

	for unitName := range skipUnits {
		for i := 0; i < len(diagramText); i++ {
			// if one of the unit names designated to be skipped was used as a dependency (x in "x --> y") in diagramText elements
			// remove the element
			if strings.Contains(diagramText[i], unitName+" -->") {
				diagramText = RemoveIndex(diagramText, i)
				i-- // decrement i to account for the removed element
			}
		}
	}
	return diagramText
}
