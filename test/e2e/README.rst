Use cases specification
#######################
Any significant new functionality has to have an end-to-end test,
which represents the use case contract. The test will test the
happy path of the use case, leaving for other tests the deviations.

The e2e tests have a docstring describing the use case using
ubiquitous language. The docstring uses `Gherkin <https://cucumber.io/docs/gherkin/reference/>`_
as syntax and has the following format:

.. code-block:: python

    def test_foo():
      """Feature: <title of the use case>
         <A small description, using the `Agile User Story template
         <https://www.agilealliance.org/glossary/user-story-template/>`_.

         <A list of scenarios that conform the use case,
         where each scenario is an interaction. `Example
         <https://cucumber.io/docs/gherkin/reference/>`_.
      """

Note that this description combines an agile user story plus the
detail of describing each scenario as an use case.

A test can have a description but yet no code, yet. Use
``@pytest.mark.skip(reason="Not developed.")`` in such case.
