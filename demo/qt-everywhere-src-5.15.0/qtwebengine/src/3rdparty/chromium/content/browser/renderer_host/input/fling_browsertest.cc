// Copyright 2018 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "base/bind.h"
#include "base/test/scoped_feature_list.h"
#include "build/build_config.h"
#include "content/browser/renderer_host/input/synthetic_smooth_scroll_gesture.h"
#include "content/browser/renderer_host/render_widget_host_input_event_router.h"
#include "content/browser/web_contents/web_contents_impl.h"
#include "content/public/test/browser_test_utils.h"
#include "content/public/test/content_browser_test.h"
#include "content/public/test/content_browser_test_utils.h"
#include "content/public/test/hit_test_region_observer.h"
#include "content/shell/browser/shell.h"
#include "content/test/content_browser_test_utils_internal.h"
#include "net/dns/mock_host_resolver.h"
#include "third_party/blink/public/platform/web_input_event.h"
#include "ui/base/ui_base_features.h"
#include "ui/events/base_event_utils.h"

using blink::WebInputEvent;

namespace {

const std::string kBrowserFlingDataURL = R"HTML(
  <!DOCTYPE html>
  <meta name='viewport' content='width=device-width'/>
  <style>
  html, body {
    margin: 0;
  }
  .spacer { height: 10000px; }
  </style>
  <div class=spacer></div>
  <script>
    document.title='ready';
  </script>)HTML";

const std::string kTouchActionFilterDataURL = R"HTML(
  <!DOCTYPE html>
  <meta name='viewport' content='width=device-width'/>
  <style>
    body {
      height: 10000px;
      touch-action: pan-y;
    }
  </style>
  <script>
    document.title='ready';
  </script>)HTML";
}  // namespace

namespace content {

class BrowserSideFlingBrowserTest : public ContentBrowserTest {
 public:
  BrowserSideFlingBrowserTest() {}
  ~BrowserSideFlingBrowserTest() override {}

  void OnSyntheticGestureCompleted(SyntheticGesture::Result result) {
    EXPECT_EQ(SyntheticGesture::GESTURE_FINISHED, result);
    run_loop_->Quit();
  }

  void SetUpOnMainThread() override {
    host_resolver()->AddRule("*", "127.0.0.1");
    SetupCrossSiteRedirector(embedded_test_server());
    ASSERT_TRUE(embedded_test_server()->Start());
  }

  void SetUpCommandLine(base::CommandLine* command_line) override {
    IsolateAllSitesForTesting(command_line);
  }

 protected:
  RenderWidgetHostImpl* GetWidgetHost() {
    return RenderWidgetHostImpl::From(
        shell()->web_contents()->GetRenderViewHost()->GetWidget());
  }

  void SynchronizeThreads() {
    MainThreadFrameObserver observer(GetWidgetHost());
    observer.Wait();
  }

  void LoadURL(const std::string& page_data) {
    const GURL data_url("data:text/html," + page_data);
    EXPECT_TRUE(NavigateToURL(shell(), data_url));

    RenderWidgetHostImpl* host = GetWidgetHost();
    host->GetView()->SetSize(gfx::Size(400, 400));

    base::string16 ready_title(base::ASCIIToUTF16("ready"));
    TitleWatcher watcher(shell()->web_contents(), ready_title);
    ignore_result(watcher.WaitAndGetTitle());
    SynchronizeThreads();
  }

  void LoadPageWithOOPIF() {
    // navigate main frame to URL.
    GURL main_url(embedded_test_server()->GetURL(
        "a.com", "/frame_tree/scrollable_page_with_positioned_frame.html"));
    EXPECT_TRUE(NavigateToURL(shell(), main_url));

    FrameTreeNode* root = static_cast<WebContentsImpl*>(shell()->web_contents())
                              ->GetFrameTree()
                              ->root();
    ASSERT_EQ(1U, root->child_count());

    // Navigate oopif to URL.
    FrameTreeNode* iframe_node = root->child_at(0);
    GURL iframe_url(embedded_test_server()->GetURL("b.com", "/tall_page.html"));
    {
      RenderFrameDeletedObserver deleted_observer(
          iframe_node->current_frame_host());
      NavigateFrameToURL(iframe_node, iframe_url);
      deleted_observer.WaitUntilDeleted();
    }

    WaitForHitTestData(iframe_node->current_frame_host());
    FrameTreeVisualizer visualizer;
    ASSERT_EQ(
        " Site A ------------ proxies for B\n"
        "   +--Site B ------- proxies for A\n"
        "Where A = http://a.com/\n"
        "      B = http://b.com/",
        visualizer.DepictFrameTree(root));

    root_view_ = static_cast<RenderWidgetHostViewBase*>(
        root->current_frame_host()->GetRenderWidgetHost()->GetView());
    child_view_ = static_cast<RenderWidgetHostViewBase*>(
        iframe_node->current_frame_host()->GetRenderWidgetHost()->GetView());
  }

  void SimulateTouchscreenFling(
      RenderWidgetHostImpl* render_widget_host,
      RenderWidgetHostImpl* parent_render_widget_host = nullptr,
      const gfx::Vector2dF& fling_velocity = gfx::Vector2dF(0.f, -2000.f)) {
    DCHECK(render_widget_host);
    // Send a GSB to start scrolling sequence. In case of scroll bubbling wait
    // for the parent to receive the GSB before sending the GFS.
    auto input_msg_watcher =
        parent_render_widget_host
            ? std::make_unique<InputMsgWatcher>(
                  parent_render_widget_host,
                  blink::WebInputEvent::kGestureScrollBegin)
            : std::make_unique<InputMsgWatcher>(
                  render_widget_host,
                  blink::WebInputEvent::kGestureScrollBegin);
    blink::WebGestureEvent gesture_scroll_begin(
        blink::WebGestureEvent::kGestureScrollBegin,
        blink::WebInputEvent::kNoModifiers, ui::EventTimeForNow());
    gesture_scroll_begin.SetSourceDevice(blink::WebGestureDevice::kTouchscreen);
    gesture_scroll_begin.data.scroll_begin.delta_hint_units =
        ui::input_types::ScrollGranularity::kScrollByPrecisePixel;
    gesture_scroll_begin.data.scroll_begin.delta_x_hint = fling_velocity.x();
    gesture_scroll_begin.data.scroll_begin.delta_y_hint = fling_velocity.y();
    const gfx::PointF scroll_location_in_widget(1, 1);
    const gfx::PointF scroll_location_in_root =
        child_view_ ? child_view_->TransformPointToRootCoordSpaceF(
                          scroll_location_in_widget)
                    : scroll_location_in_widget;
    const gfx::PointF scroll_location_in_screen =
        child_view_ ? scroll_location_in_root +
                          root_view_->GetViewBounds().OffsetFromOrigin()
                    : scroll_location_in_widget;
    gesture_scroll_begin.SetPositionInWidget(scroll_location_in_widget);
    gesture_scroll_begin.SetPositionInScreen(scroll_location_in_screen);
    render_widget_host->ForwardGestureEvent(gesture_scroll_begin);
    input_msg_watcher->GetAckStateWaitIfNecessary();

    //  Send a GFS.
    blink::WebGestureEvent gesture_fling_start(
        blink::WebGestureEvent::kGestureFlingStart,
        blink::WebInputEvent::kNoModifiers, ui::EventTimeForNow());
    gesture_fling_start.SetSourceDevice(blink::WebGestureDevice::kTouchscreen);
    gesture_fling_start.data.fling_start.velocity_x = fling_velocity.x();
    gesture_fling_start.data.fling_start.velocity_y = fling_velocity.y();
    gesture_fling_start.SetPositionInWidget(scroll_location_in_widget);
    gesture_fling_start.SetPositionInScreen(scroll_location_in_screen);
    render_widget_host->ForwardGestureEvent(gesture_fling_start);
  }

  void SimulateTouchpadFling(
      RenderWidgetHostImpl* render_widget_host,
      RenderWidgetHostImpl* parent_render_widget_host = nullptr,
      const gfx::Vector2dF& fling_velocity = gfx::Vector2dF(0.f, -2000.f)) {
    DCHECK(render_widget_host);
    // Send a wheel event to start scrolling sequence. In case of scroll
    // bubbling wait for the parent to receive the GSB before sending the GFS.
    auto input_msg_watcher =
        parent_render_widget_host
            ? std::make_unique<InputMsgWatcher>(
                  parent_render_widget_host,
                  blink::WebInputEvent::kGestureScrollBegin)
            : std::make_unique<InputMsgWatcher>(
                  render_widget_host,
                  blink::WebInputEvent::kGestureScrollBegin);
    blink::WebMouseWheelEvent wheel_event =
        SyntheticWebMouseWheelEventBuilder::Build(
            10, 10, fling_velocity.x() / 1000, fling_velocity.y() / 1000, 0,
            ui::input_types::ScrollGranularity::kScrollByPrecisePixel);
    wheel_event.phase = blink::WebMouseWheelEvent::kPhaseBegan;
    const gfx::PointF position_in_widget(1, 1);
    const gfx::PointF position_in_root =
        child_view_
            ? child_view_->TransformPointToRootCoordSpaceF(position_in_widget)
            : position_in_widget;
    const gfx::PointF position_in_screen =
        child_view_
            ? position_in_root + root_view_->GetViewBounds().OffsetFromOrigin()
            : position_in_widget;
    wheel_event.SetPositionInWidget(position_in_widget);
    wheel_event.SetPositionInScreen(position_in_screen);
    render_widget_host->ForwardWheelEvent(wheel_event);
    input_msg_watcher->GetAckStateWaitIfNecessary();

    //  Send a GFS.
    blink::WebGestureEvent gesture_fling_start(
        blink::WebGestureEvent::kGestureFlingStart,
        blink::WebInputEvent::kNoModifiers, ui::EventTimeForNow());
    gesture_fling_start.SetSourceDevice(blink::WebGestureDevice::kTouchpad);
    gesture_fling_start.data.fling_start.velocity_x = fling_velocity.x();
    gesture_fling_start.data.fling_start.velocity_y = fling_velocity.y();
    gesture_fling_start.SetPositionInWidget(position_in_widget);
    gesture_fling_start.SetPositionInScreen(position_in_screen);
    render_widget_host->ForwardGestureEvent(gesture_fling_start);
  }

  void WaitForScroll() {
    RenderFrameSubmissionObserver observer(
        GetWidgetHost()->render_frame_metadata_provider());
    gfx::Vector2dF default_scroll_offset;
    // scrollTop > 0 is not enough since the first progressFling is called from
    // FlingController::ProcessGestureFlingStart. Wait for scrollTop to exceed
    // 100 pixels to make sure that ProgressFling has been called through
    // FlingScheduler at least once.
    while (observer.LastRenderFrameMetadata()
               .root_scroll_offset.value_or(default_scroll_offset)
               .y() <= 100) {
      observer.WaitForMetadataChange();
    }
  }

  void GiveItSomeTime(int64_t time_delta_ms = 10) {
    base::RunLoop run_loop;
    base::ThreadTaskRunnerHandle::Get()->PostDelayedTask(
        FROM_HERE, run_loop.QuitClosure(),
        base::TimeDelta::FromMilliseconds(time_delta_ms));
    run_loop.Run();
  }

  void WaitForFrameScroll(FrameTreeNode* frame_node,
                          int target_scroll_offset = 100,
                          bool upward = false) {
    DCHECK(frame_node);
    double scroll_top =
        EvalJs(frame_node->current_frame_host(), "window.scrollY")
            .ExtractDouble();
    // scrollTop > 0 is not enough since the first progressFling is called from
    // FlingController::ProcessGestureFlingStart. Wait for scrollTop to reach
    // target_scroll_offset to make sure that ProgressFling has been called
    // through FlingScheduler at least once.
    while ((upward && scroll_top > target_scroll_offset) ||
           (!upward && scroll_top < target_scroll_offset)) {
      GiveItSomeTime();
      scroll_top = EvalJs(frame_node->current_frame_host(), "window.scrollY")
                       .ExtractDouble();
    }
  }

  FrameTreeNode* GetRootNode() {
    return static_cast<WebContentsImpl*>(shell()->web_contents())
        ->GetFrameTree()
        ->root();
  }

  FrameTreeNode* GetChildNode() {
    FrameTreeNode* root = GetRootNode();
    return root->child_at(0);
  }

  std::unique_ptr<base::RunLoop> run_loop_;
  RenderWidgetHostViewBase* child_view_ = nullptr;
  RenderWidgetHostViewBase* root_view_ = nullptr;

 private:
  DISALLOW_COPY_AND_ASSIGN(BrowserSideFlingBrowserTest);
};

// On Mac we don't have any touchscreen/touchpad fling events (GFS/GFC).
// Instead, the OS keeps sending wheel events when the user lifts their fingers
// from touchpad.
#if !defined(OS_MACOSX)
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest, TouchscreenFling) {
  LoadURL(kBrowserFlingDataURL);
  SimulateTouchscreenFling(GetWidgetHost());
  WaitForScroll();
}
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest, TouchpadFling) {
  LoadURL(kBrowserFlingDataURL);
  SimulateTouchpadFling(GetWidgetHost());
  WaitForScroll();
}
IN_PROC_BROWSER_TEST_F(
    BrowserSideFlingBrowserTest,
    EarlyTouchscreenFlingCancelationOnInertialGSUAckNotConsumed) {
  LoadURL(kBrowserFlingDataURL);

  // Fling upward and wait for the generated GSE to arrive. Then check that the
  // RWHV has stopped the fling.
  auto input_msg_watcher = std::make_unique<InputMsgWatcher>(
      GetWidgetHost(), blink::WebInputEvent::kGestureScrollEnd);
  gfx::Vector2d fling_velocity(0, 2000);
  SimulateTouchscreenFling(
      GetWidgetHost(), nullptr /*parent_render_widget_host*/, fling_velocity);
  input_msg_watcher->GetAckStateWaitIfNecessary();
  EXPECT_TRUE(GetWidgetHost()->GetView()->view_stopped_flinging_for_test());
}
IN_PROC_BROWSER_TEST_F(
    BrowserSideFlingBrowserTest,
    EarlyTouchpadFlingCancelationOnInertialGSUAckNotConsumed) {
  LoadURL(kBrowserFlingDataURL);

  // Fling upward and wait for the generated GSE to arrive. Then check that the
  // RWHV has stopped the fling.
  auto input_msg_watcher = std::make_unique<InputMsgWatcher>(
      GetWidgetHost(), blink::WebInputEvent::kGestureScrollEnd);
  gfx::Vector2d fling_velocity(0, 2000);
  SimulateTouchpadFling(GetWidgetHost(), nullptr /*parent_render_widget_host*/,
                        fling_velocity);
  input_msg_watcher->GetAckStateWaitIfNecessary();
  EXPECT_TRUE(GetWidgetHost()->GetView()->view_stopped_flinging_for_test());
}

// Tests that flinging does not continue after navigating to a page that uses
// the same renderer.
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest,
                       FlingingStopsAfterNavigation) {
  GURL first_url(embedded_test_server()->GetURL(
      "b.a.com", "/scrollable_page_with_iframe.html"));
  EXPECT_TRUE(NavigateToURL(shell(), first_url));
  SynchronizeThreads();
  SimulateTouchscreenFling(GetWidgetHost());
  WaitForScroll();

  // Navigate to a second page with the same domain.
  GURL second_url(
      embedded_test_server()->GetURL("a.com", "/scrollable_page.html"));
  EXPECT_TRUE(NavigateToURL(shell(), second_url));
  SynchronizeThreads();

  // Wait for 100ms. Then check that the second page has not scrolled.
  GiveItSomeTime(100);
  FrameTreeNode* root = static_cast<WebContentsImpl*>(shell()->web_contents())
                            ->GetFrameTree()
                            ->root();
  EXPECT_EQ(
      0, EvalJs(root->current_frame_host(), "window.scrollY").ExtractDouble());
}

IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest, TouchscreenFlingInOOPIF) {
  LoadPageWithOOPIF();
  SimulateTouchscreenFling(child_view_->host());
  WaitForFrameScroll(GetChildNode());
}
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest, TouchpadFlingInOOPIF) {
  LoadPageWithOOPIF();
  SimulateTouchpadFling(child_view_->host());
  WaitForFrameScroll(GetChildNode());
}
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest,
                       TouchscreenInertialGSUsBubbleFromOOPIF) {
  LoadPageWithOOPIF();
  // Scroll the parent down so that it is scrollable upward.
  EXPECT_TRUE(
      ExecJs(GetRootNode()->current_frame_host(), "window.scrollTo(0, 20)"));
  // We expect to have window.scrollY == 20 after scrolling but with zoom for
  // dsf enabled on android we get window.scrollY == 19 (see
  // https://crbug.com/891860).
  WaitForFrameScroll(GetRootNode(), 19);
  SynchronizeThreads();

  // Fling and wait for the parent to scroll upward.
  gfx::Vector2d fling_velocity(0, 2000);
  SimulateTouchscreenFling(child_view_->host(), GetWidgetHost(),
                           fling_velocity);
  WaitForFrameScroll(GetRootNode(), 15, true /* upward */);
}

// Touchpad fling only happens on ChromeOS.
#if defined(CHROMEOS)
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest,
                       TouchpadInertialGSUsBubbleFromOOPIF) {
  LoadPageWithOOPIF();
  // Scroll the parent down so that it is scrollable upward.
  EXPECT_TRUE(
      ExecJs(GetRootNode()->current_frame_host(), "window.scrollTo(0, 20)"));
  // We expect to have window.scrollY == 20 after scrolling but with zoom for
  // dsf enabled on android we get window.scrollY == 19 (see
  // https://crbug.com/891860).
  WaitForFrameScroll(GetRootNode(), 19);
  SynchronizeThreads();

  // Fling and wait for the parent to scroll upward.
  gfx::Vector2d fling_velocity(0, 2000);
  SimulateTouchpadFling(child_view_->host(), GetWidgetHost(), fling_velocity);
  WaitForFrameScroll(GetRootNode(), 15, true /* upward */);
}
#endif  // defined(CHROMEOS)

IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest,
                       InertialGSEGetsBubbledFromOOPIF) {
  LoadPageWithOOPIF();
  // Scroll the parent down so that it is scrollable upward.
  EXPECT_TRUE(
      ExecJs(GetRootNode()->current_frame_host(), "window.scrollTo(0, 20)"));
  // We expect to have window.scrollY == 20 after scrolling but with zoom for
  // dsf enabled on android we get window.scrollY == 19 (see
  // https://crbug.com/891860).
  WaitForFrameScroll(GetRootNode(), 19);
  SynchronizeThreads();

  // Fling and wait for the parent to scroll upward.
  gfx::Vector2d fling_velocity(0, 2000);
  SimulateTouchscreenFling(child_view_->host(), GetWidgetHost(),
                           fling_velocity);
  WaitForFrameScroll(GetRootNode(), 15, true /* upward */);

  // Send a GFC to the child and wait for the Generated GSE to get bubbled.
  auto input_msg_watcher = std::make_unique<InputMsgWatcher>(
      GetWidgetHost(), blink::WebInputEvent::kGestureScrollEnd);
  blink::WebGestureEvent gesture_fling_cancel(
      blink::WebGestureEvent::kGestureFlingCancel,
      blink::WebInputEvent::kNoModifiers, ui::EventTimeForNow());
  gesture_fling_cancel.SetSourceDevice(blink::WebGestureDevice::kTouchscreen);

  const gfx::PointF location_in_widget(1, 1);
  const gfx::PointF location_in_root =
      child_view_->TransformPointToRootCoordSpaceF(location_in_widget);
  const gfx::PointF location_in_screen =
      location_in_root + root_view_->GetViewBounds().OffsetFromOrigin();
  gesture_fling_cancel.SetPositionInWidget(location_in_widget);
  gesture_fling_cancel.SetPositionInScreen(location_in_screen);
  child_view_->host()->ForwardGestureEvent(gesture_fling_cancel);
  input_msg_watcher->GetAckStateWaitIfNecessary();
}

// Checks that the fling controller of the oopif stops the fling when the
// bubbled inertial GSUs are not consumed by the parent's renderer.
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest,
                       InertialGSUBubblingStopsWhenParentCannotScroll) {
  LoadPageWithOOPIF();
  // Scroll the parent down so that it is scrollable upward.

  // Initialize observer before scrolling changes the position of the OOPIF.
  HitTestRegionObserver observer(child_view_->GetFrameSinkId());
  observer.WaitForHitTestData();

  EXPECT_TRUE(
      ExecJs(GetRootNode()->current_frame_host(), "window.scrollTo(0, 20)"));
  // We expect to have window.scrollY == 20 after scrolling but with zoom for
  // dsf enabled on android we get window.scrollY == 19 (see
  // https://crbug.com/891860).
  WaitForFrameScroll(GetRootNode(), 19);
  SynchronizeThreads();

  observer.WaitForHitTestDataChange();

  // Fling and wait for the parent to scroll up.
  auto input_msg_watcher = std::make_unique<InputMsgWatcher>(
      GetWidgetHost(), blink::WebInputEvent::kGestureScrollEnd);
  SyntheticSmoothScrollGestureParams params;
  params.gesture_source_type = SyntheticGestureParams::TOUCH_INPUT;
  const gfx::PointF location_in_widget(10, 10);
  const gfx::PointF location_in_root =
      child_view_->TransformPointToRootCoordSpaceF(location_in_widget);
  const gfx::PointF location_in_screen =
      location_in_root + root_view_->GetViewBounds().OffsetFromOrigin();
  params.anchor = location_in_screen;
  params.distances.push_back(gfx::Vector2d(0, 100));
  params.prevent_fling = false;

  run_loop_ = std::make_unique<base::RunLoop>();

  GetWidgetHost()->QueueSyntheticGesture(
      std::make_unique<SyntheticSmoothScrollGesture>(params),
      base::BindOnce(&BrowserSideFlingBrowserTest::OnSyntheticGestureCompleted,
                     base::Unretained(this)));

  // Runs until we get the OnSyntheticGestureCompleted callback.
  run_loop_->Run();

  // Wait for the Generated GSE to get bubbled.
  input_msg_watcher->GetAckStateWaitIfNecessary();

  // Check that the router has forced the last fling start target to stop
  // flinging.
  RenderWidgetHostInputEventRouter* router =
      static_cast<WebContentsImpl*>(shell()->web_contents())
          ->GetInputEventRouter();
  EXPECT_TRUE(
      router->forced_last_fling_start_target_to_stop_flinging_for_test());
}

// Check that fling controller does not generate fling curve when view is
// destroyed.
IN_PROC_BROWSER_TEST_F(BrowserSideFlingBrowserTest,
                       NoFlingWhenViewIsDestroyed) {
  LoadURL(kBrowserFlingDataURL);
  FrameTreeNode* root = static_cast<WebContentsImpl*>(shell()->web_contents())
                            ->GetFrameTree()
                            ->root();

  GetWidgetHost()->GetView()->Destroy();
  SimulateTouchscreenFling(GetWidgetHost());

  // As the view is destroyed, there shouldn't be any active fling.
  EXPECT_FALSE(static_cast<InputRouterImpl*>(GetWidgetHost()->input_router())
                   ->IsFlingActiveForTest());

  EXPECT_EQ(
      0, EvalJs(root->current_frame_host(), "window.scrollY").ExtractDouble());
}
#endif  // !defined(OS_MACOSX)

class PhysicsBasedFlingCurveBrowserTest : public BrowserSideFlingBrowserTest {
 public:
  PhysicsBasedFlingCurveBrowserTest() {}
  ~PhysicsBasedFlingCurveBrowserTest() override {}

  void SetUpCommandLine(base::CommandLine* command_line) override {
    scoped_feature_list_.InitWithFeatures(
        {features::kExperimentalFlingAnimation}, {});
    IsolateAllSitesForTesting(command_line);
  }

 private:
  base::test::ScopedFeatureList scoped_feature_list_;
  DISALLOW_COPY_AND_ASSIGN(PhysicsBasedFlingCurveBrowserTest);
};

IN_PROC_BROWSER_TEST_F(PhysicsBasedFlingCurveBrowserTest,
                       TargetScrollOffsetForFlingAnimation) {
  LoadPageWithOOPIF();

  // Higher value of fling velocity will make sure that the scroll distance
  // calculated exceeds the upper bound.
  gfx::Vector2d fling_velocity(0, -6000.0);

  // Simulate fling on OOPIF
  SimulateTouchscreenFling(child_view_->host(), nullptr, fling_velocity);

  // If the viewport size required for fling curve generation
  // (PhysicsBasedFlingCurveBrowser) is based on RenderWidget, test will time
  // out as upper bound calculated will be 3 * size of iframe window(3 * 100)
  // and thus it will not scroll beyond it. Viewport size should be based on
  // root RenderWidgetHost.
  WaitForFrameScroll(GetChildNode(), 400);
}

}  // namespace content