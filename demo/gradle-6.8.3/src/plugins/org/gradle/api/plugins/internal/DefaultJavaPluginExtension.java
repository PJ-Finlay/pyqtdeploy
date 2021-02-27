/*
 * Copyright 2018 the original author or authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.gradle.api.plugins.internal;

import com.google.common.collect.ImmutableList;
import org.gradle.api.Action;
import org.gradle.api.InvalidUserDataException;
import org.gradle.api.JavaVersion;
import org.gradle.api.Project;
import org.gradle.api.artifacts.Configuration;
import org.gradle.api.artifacts.ConfigurationContainer;
import org.gradle.api.capabilities.Capability;
import org.gradle.api.component.SoftwareComponentContainer;
import org.gradle.api.jvm.ModularitySpec;
import org.gradle.api.model.ObjectFactory;
import org.gradle.api.plugins.FeatureSpec;
import org.gradle.api.plugins.JavaPluginConvention;
import org.gradle.api.plugins.JavaPluginExtension;
import org.gradle.api.plugins.JavaResolutionConsistency;
import org.gradle.api.plugins.jvm.internal.JvmPluginServices;
import org.gradle.api.tasks.SourceSet;
import org.gradle.api.tasks.SourceSetContainer;
import org.gradle.api.tasks.TaskContainer;
import org.gradle.internal.component.external.model.ProjectDerivedCapability;
import org.gradle.internal.jvm.DefaultModularitySpec;
import org.gradle.jvm.toolchain.JavaToolchainSpec;

import javax.inject.Inject;
import java.util.regex.Pattern;

import static org.gradle.api.attributes.DocsType.JAVADOC;
import static org.gradle.api.attributes.DocsType.SOURCES;
import static org.gradle.api.plugins.JavaPlugin.JAVADOC_ELEMENTS_CONFIGURATION_NAME;
import static org.gradle.api.plugins.JavaPlugin.SOURCES_ELEMENTS_CONFIGURATION_NAME;
import static org.gradle.api.plugins.internal.JvmPluginsHelper.configureDocumentationVariantWithArtifact;
import static org.gradle.api.plugins.internal.JvmPluginsHelper.findJavaComponent;

public class DefaultJavaPluginExtension implements JavaPluginExtension {
    private final static Pattern VALID_FEATURE_NAME = Pattern.compile("[a-zA-Z0-9]+");

    private final JavaPluginConvention convention;
    private final ObjectFactory objectFactory;
    private final SoftwareComponentContainer components;
    private final Project project;
    private final ModularitySpec modularity;
    private final JvmPluginServices jvmPluginServices;
    private final JavaToolchainSpec toolchain;

    public DefaultJavaPluginExtension(JavaPluginConvention convention,
                                      Project project,
                                      JvmPluginServices jvmPluginServices,
                                      JavaToolchainSpec toolchainSpec) {
        this.convention = convention;
        this.objectFactory = project.getObjects();
        this.components = project.getComponents();
        this.project = project;
        this.modularity = objectFactory.newInstance(DefaultModularitySpec.class);
        this.jvmPluginServices = jvmPluginServices;
        this.toolchain = toolchainSpec;
    }

    @Override
    public JavaVersion getSourceCompatibility() {
        return convention.getSourceCompatibility();
    }

    @Override
    public void setSourceCompatibility(JavaVersion value) {
        convention.setSourceCompatibility(value);
    }

    @Override
    public JavaVersion getTargetCompatibility() {
        return convention.getTargetCompatibility();
    }

    @Override
    public void setTargetCompatibility(JavaVersion value) {
        convention.setTargetCompatibility(value);
    }

    @Override
    public void registerFeature(String name, Action<? super FeatureSpec> configureAction) {
        Capability defaultCapability = new ProjectDerivedCapability(project, name);
        DefaultJavaFeatureSpec spec = new DefaultJavaFeatureSpec(
            validateFeatureName(name),
            defaultCapability,
            jvmPluginServices);
        configureAction.execute(spec);
        spec.create();
    }

    @Override
    public void disableAutoTargetJvm() {
        convention.disableAutoTargetJvm();
    }

    @Override
    public void withJavadocJar() {
        TaskContainer tasks = project.getTasks();
        ConfigurationContainer configurations = project.getConfigurations();
        SourceSet main = convention.getSourceSets().getByName(SourceSet.MAIN_SOURCE_SET_NAME);
        configureDocumentationVariantWithArtifact(JAVADOC_ELEMENTS_CONFIGURATION_NAME, null, JAVADOC, ImmutableList.of(), main.getJavadocJarTaskName(), tasks.named(main.getJavadocTaskName()), findJavaComponent(components), configurations, tasks, objectFactory);
    }

    @Override
    public void withSourcesJar() {
        TaskContainer tasks = project.getTasks();
        ConfigurationContainer configurations = project.getConfigurations();
        SourceSet main = convention.getSourceSets().getByName(SourceSet.MAIN_SOURCE_SET_NAME);
        configureDocumentationVariantWithArtifact(SOURCES_ELEMENTS_CONFIGURATION_NAME, null, SOURCES, ImmutableList.of(), main.getSourcesJarTaskName(), main.getAllSource(), findJavaComponent(components), configurations, tasks, objectFactory);
    }

    @Override
    public ModularitySpec getModularity() {
        return modularity;
    }

    @Override
    public JavaToolchainSpec getToolchain() {
        return toolchain;
    }

    @Override
    public JavaToolchainSpec toolchain(Action<? super JavaToolchainSpec> action) {
        action.execute(toolchain);
        return toolchain;
    }

    @Override
    public void consistentResolution(Action<? super JavaResolutionConsistency> action) {
        final ConfigurationContainer configurations = project.getConfigurations();
        final SourceSetContainer sourceSets = convention.getSourceSets();

        action.execute(project.getObjects().newInstance(DefaultJavaResolutionConsistency.class, sourceSets, configurations));
    }

    private static String validateFeatureName(String name) {
        if (!VALID_FEATURE_NAME.matcher(name).matches()) {
            throw new InvalidUserDataException("Invalid feature name '" + name + "'. Must match " + VALID_FEATURE_NAME.pattern());
        }
        return name;
    }

    public static class DefaultJavaResolutionConsistency implements JavaResolutionConsistency {
        private final Configuration mainCompileClasspath;
        private final Configuration mainRuntimeClasspath;
        private final Configuration testCompileClasspath;
        private final Configuration testRuntimeClasspath;
        private final SourceSetContainer sourceSets;
        private final ConfigurationContainer configurations;

        @Inject
        public DefaultJavaResolutionConsistency(SourceSetContainer sourceSets, ConfigurationContainer configurations) {
            this.sourceSets = sourceSets;
            this.configurations = configurations;
            SourceSet mainSourceSet = sourceSets.getByName(SourceSet.MAIN_SOURCE_SET_NAME);
            SourceSet testSourceSet = sourceSets.getByName(SourceSet.TEST_SOURCE_SET_NAME);
            mainCompileClasspath = findConfiguration(mainSourceSet.getCompileClasspathConfigurationName());
            mainRuntimeClasspath = findConfiguration(mainSourceSet.getRuntimeClasspathConfigurationName());
            testCompileClasspath = findConfiguration(testSourceSet.getCompileClasspathConfigurationName());
            testRuntimeClasspath = findConfiguration(testSourceSet.getRuntimeClasspathConfigurationName());
        }

        @Override
        public void useCompileClasspathVersions() {
            sourceSets.configureEach(this::applyCompileClasspathConsistency);
            testCompileClasspath.shouldResolveConsistentlyWith(mainCompileClasspath);
        }

        @Override
        public void useRuntimeClasspathVersions() {
            sourceSets.configureEach(this::applyRuntimeClasspathConsistency);
            testRuntimeClasspath.shouldResolveConsistentlyWith(mainRuntimeClasspath);
        }

        private void applyCompileClasspathConsistency(SourceSet sourceSet) {
            Configuration compileClasspath = findConfiguration(sourceSet.getCompileClasspathConfigurationName());
            Configuration runtimeClasspath = findConfiguration(sourceSet.getRuntimeClasspathConfigurationName());
            runtimeClasspath.shouldResolveConsistentlyWith(compileClasspath);
        }

        private void applyRuntimeClasspathConsistency(SourceSet sourceSet) {
            Configuration compileClasspath = findConfiguration(sourceSet.getCompileClasspathConfigurationName());
            Configuration runtimeClasspath = findConfiguration(sourceSet.getRuntimeClasspathConfigurationName());
            compileClasspath.shouldResolveConsistentlyWith(runtimeClasspath);
        }

        private Configuration findConfiguration(String configName) {
            return configurations.getByName(configName);
        }
    }
}
