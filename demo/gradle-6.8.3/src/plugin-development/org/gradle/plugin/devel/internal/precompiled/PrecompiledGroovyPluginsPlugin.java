/*
 * Copyright 2020 the original author or authors.
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

package org.gradle.plugin.devel.internal.precompiled;

import org.gradle.api.Plugin;
import org.gradle.api.Project;
import org.gradle.api.file.DirectoryProperty;
import org.gradle.api.file.FileTree;
import org.gradle.api.file.SourceDirectorySet;
import org.gradle.api.internal.plugins.DslObject;
import org.gradle.api.plugins.GroovyBasePlugin;
import org.gradle.api.tasks.GroovySourceSet;
import org.gradle.api.tasks.SourceSet;
import org.gradle.api.tasks.TaskContainer;
import org.gradle.api.tasks.TaskProvider;
import org.gradle.internal.resource.TextFileResourceLoader;
import org.gradle.plugin.devel.GradlePluginDevelopmentExtension;
import org.gradle.plugin.devel.plugins.JavaGradlePluginPlugin;

import javax.inject.Inject;
import java.util.List;
import java.util.stream.Collectors;

public abstract class PrecompiledGroovyPluginsPlugin implements Plugin<Project> {
    @Override
    public void apply(Project project) {
        project.getPluginManager().apply(GroovyBasePlugin.class);
        project.getPluginManager().apply(JavaGradlePluginPlugin.class);

        project.afterEvaluate(this::exposeScriptsAsPlugins);
    }

    @Inject
    protected abstract TextFileResourceLoader getTextFileResourceLoader();

    private void exposeScriptsAsPlugins(Project project) {
        GradlePluginDevelopmentExtension pluginExtension = project.getExtensions().getByType(GradlePluginDevelopmentExtension.class);

        SourceSet pluginSourceSet = pluginExtension.getPluginSourceSet();
        FileTree scriptPluginFiles = pluginSourceSet.getAllSource().matching(PrecompiledGroovyScript::filterPluginFiles);

        List<PrecompiledGroovyScript> scriptPlugins = scriptPluginFiles.getFiles().stream()
            .map(file -> new PrecompiledGroovyScript(file, getTextFileResourceLoader()))
            .collect(Collectors.toList());

        declarePluginMetadata(pluginExtension, scriptPlugins);

        DirectoryProperty buildDir = project.getLayout().getBuildDirectory();
        TaskContainer tasks = project.getTasks();

        TaskProvider<ExtractPluginRequestsTask> extractPluginRequests = tasks.register("extractPluginRequests", ExtractPluginRequestsTask.class, task -> {
            task.getScriptPlugins().convention(scriptPlugins);
            task.getScriptFiles().from(scriptPluginFiles.getFiles());
            task.getExtractedPluginRequestsClassesDirectory().convention(buildDir.dir("groovy-dsl-plugins/plugin-requests"));
        });

        TaskProvider<GeneratePluginAdaptersTask> generatePluginAdapters = tasks.register("generatePluginAdapters", GeneratePluginAdaptersTask.class, task -> {
            task.getScriptPlugins().convention(scriptPlugins);
            task.getExtractedPluginRequestsClassesDirectory().convention(extractPluginRequests.flatMap(ExtractPluginRequestsTask::getExtractedPluginRequestsClassesDirectory));
            task.getPluginAdapterSourcesOutputDirectory().convention(buildDir.dir("groovy-dsl-plugins/output/adapter-src"));
        });

        TaskProvider<CompileGroovyScriptPluginsTask> precompilePlugins = tasks.register("compileGroovyPlugins", CompileGroovyScriptPluginsTask.class, task -> {
            task.getScriptPlugins().convention(scriptPlugins);
            task.getScriptFiles().from(scriptPluginFiles.getFiles());
            task.getPrecompiledGroovyScriptsOutputDirectory().convention(buildDir.dir("groovy-dsl-plugins/output/plugin-classes"));

            SourceDirectorySet javaSource = pluginSourceSet.getJava();
            SourceDirectorySet groovySource = new DslObject(pluginSourceSet).getConvention().getPlugin(GroovySourceSet.class).getGroovy();
            task.getClasspath().from(pluginSourceSet.getCompileClasspath(), javaSource.getClassesDirectory(), groovySource.getClassesDirectory());
        });

        pluginSourceSet.getJava().srcDir(generatePluginAdapters.flatMap(GeneratePluginAdaptersTask::getPluginAdapterSourcesOutputDirectory));
        pluginSourceSet.getOutput().dir(precompilePlugins.flatMap(CompileGroovyScriptPluginsTask::getPrecompiledGroovyScriptsOutputDirectory));
    }

    private void declarePluginMetadata(GradlePluginDevelopmentExtension pluginExtension, List<PrecompiledGroovyScript> scriptPlugins) {
        pluginExtension.plugins(pluginDeclarations ->
            scriptPlugins.forEach(scriptPlugin ->
                pluginDeclarations.create(scriptPlugin.getId(), scriptPlugin::declarePlugin)));
    }
}
